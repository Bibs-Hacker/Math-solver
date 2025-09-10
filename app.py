from flask import Flask, render_template, request, jsonify
from sympy import (
    sympify, Symbol, Eq, solve, simplify, diff, integrate, pretty, solveset,
    S, N, latex
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)
import traceback

app = Flask(__name__, static_folder="static", template_folder="templates")

TRANSFORMS = (standard_transformations + (implicit_multiplication_application,))

def safe_parse(expr_str):
    """
    Parse an expression string into a SymPy expression using safe transforms.
    """
    expr_str = expr_str.strip()
    if not expr_str:
        raise ValueError("Empty expression")
    return parse_expr(expr_str, transformations=TRANSFORMS, evaluate=True)

def analyze_input(text):
    """
    Determine intent: equation, derivative, integral, simplify, evaluate, or algebraic expression.
    Very simple heuristics based on keywords/symbols.
    Returns a dict: {mode: str, expr: str, var: str (optional)}
    """
    lower = text.lower()
    # common cues:
    if "deriv" in lower or "d/d" in lower or "differentiate" in lower:
        return {"mode":"diff", "expr":text}
    if "integral" in lower or "integrate" in lower or "∫" in text:
        return {"mode":"integrate", "expr":text}
    if "simplify" in lower or "simplify(" in lower:
        return {"mode":"simplify", "expr":text}
    if "=" in text and "==" not in text and "=>" not in text:
        return {"mode":"equation", "expr":text}
    # numeric evaluate request
    if lower.startswith("eval") or lower.startswith("evaluate") or "calculate" in lower:
        return {"mode":"eval", "expr":text}
    # default guess: try to parse as expression (eval or simplify)
    return {"mode":"auto", "expr":text}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/solve", methods=["POST"])
def api_solve():
    data = request.json or {}
    text = (data.get("query") or "").strip()
    if not text:
        return jsonify({"ok":False, "error":"Empty query"}), 400

    try:
        intent = analyze_input(text)
        mode = intent["mode"]

        # Clean expression string
        expr_str = text

        # Quick heuristics for derivative/integral with short syntax
        # Users may type: d/dx x^2  or derivative x^2 wrt x
        # We try to extract variable if provided
        result = {"ok":True, "input": text, "mode": mode}

        if mode == "equation":
            # split at '='; support single equation or system if user separates with ';'
            equations = [s.strip() for s in expr_str.split(";") if s.strip()]
            sols = []
            for eq in equations:
                if "=" not in eq:
                    # treat as expression = 0
                    lhs = safe_parse(eq)
                    s = solve(lhs, dict=True)
                    sols.append({"equation": eq, "solutions": s})
                else:
                    left,right = eq.split("=",1)
                    L = safe_parse(left)
                    R = safe_parse(right)
                    s = solve(Eq(L,R), dict=True)
                    sols.append({"equation": eq, "solutions": s})
            result["result"] = sols
            return jsonify(result)

        if mode == "diff":
            # try to capture variable like d/dx f(x) or derivative f(x), x
            # naive: if contains "d/d" extract variable
            var = None
            if "d/d" in expr_str:
                try:
                    after = expr_str.split("d/d",1)[1].strip()
                    var = after[0]
                    remaining = expr_str.split("d/d"+after,1)[1] if ("d/d"+after) in expr_str else expr_str
                except:
                    remaining = expr_str
            else:
                remaining = expr_str

            # attempt to split "differentiate <expr> wrt x" or "derivative <expr>, x"
            import re
            m = re.search(r"wrt\s*([a-zA-Z])", expr_str)
            if m:
                var = m.group(1)
                remaining = expr_str

            # find expression inside keyword
            # fallback: take the last token as variable if comma-separated
            if "," in expr_str:
                parts = [p.strip() for p in expr_str.split(",")]
                if len(parts)>=2 and len(parts[-1])==1 and parts[-1].isalpha():
                    var = parts[-1]
                    remaining = ",".join(parts[:-1])

            # parse expression (remove "differentiate" or "derivative" words)
            cleaned = expr_str.replace("differentiate","").replace("derivative","").replace("d/d"+(var or ""),"")
            expr = safe_parse(cleaned)
            var_sym = Symbol(var) if var else list(expr.free_symbols)[0] if expr.free_symbols else Symbol('x')
            out = diff(expr, var_sym)
            result["result"] = {"input_expr": str(expr), "variable": str(var_sym), "derivative": str(out), "latex": latex(out)}
            return jsonify(result)

        if mode == "integrate":
            # similar heuristics as diff
            import re
            var = None
            m = re.search(r"wrt\s*([a-zA-Z])", expr_str)
            if m: var = m.group(1)
            if "," in expr_str:
                parts = [p.strip() for p in expr_str.split(",")]
                if len(parts)>=2 and len(parts[-1])==1 and parts[-1].isalpha():
                    var = parts[-1]
                    expr_str = ",".join(parts[:-1])
            cleaned = expr_str.replace("integrate","").replace("integral","").replace("∫","")
            expr = safe_parse(cleaned)
            var_sym = Symbol(var) if var else (list(expr.free_symbols)[0] if expr.free_symbols else Symbol('x'))
            out = integrate(expr, var_sym)
            result["result"] = {"input_expr": str(expr), "variable": str(var_sym), "integral": str(out), "latex": latex(out)}
            return jsonify(result)

        if mode == "simplify":
            cleaned = expr_str.replace("simplify","")
            expr = safe_parse(cleaned)
            out = simplify(expr)
            result["result"] = {"input": str(expr), "simplified": str(out), "latex": latex(out)}
            return jsonify(result)

        if mode == "eval" or mode == "auto":
            # try to evaluate numerically if values present, else simplify
            # if contains "=", route to equation handler above
            try:
                expr = safe_parse(expr_str)
                # numeric if contains no free symbols
                if not expr.free_symbols:
                    val = N(expr)
                    result["result"] = {"type":"numeric","value":str(val)}
                    return jsonify(result)
                else:
                    # symbolic simplify
                    out = simplify(expr)
                    result["result"] = {"type":"symbolic","simplified":str(out)}
                    return jsonify(result)
            except Exception as e:
                # as a fallback, attempt to detect "solve for" pattern like "solve x^2-4=0 for x"
                if "solve" in expr_str.lower():
                    try:
                        import re
                        m = re.search(r"for\s+([a-zA-Z])", expr_str.lower())
                        var = m.group(1) if m else None
                        eq_part = expr_str.lower().replace("solve","").strip()
                        if "=" in eq_part:
                            left,right = eq_part.split("=",1)
                            L = safe_parse(left)
                            R = safe_parse(right)
                            sol = solve(Eq(L,R), Symbol(var) if var else None)
                            result["result"] = sol
                            return jsonify(result)
                    except Exception:
                        pass
                raise

        # fallback not covered
        return jsonify({"ok":False, "error":"Could not determine operation or failed to compute. Try clearer math syntax (e.g. 'integrate x^2', 'differentiate sin(x) wrt x', 'solve x^2-1=0')"}), 400

    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"ok":False, "error": str(e), "trace": tb}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
