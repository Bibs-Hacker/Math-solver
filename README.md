# Math-solver
Brian's Math Solver
===================
<p align="center">
  <img src="https://files.catbox.moe/b2xl1t.jpg" width="500"/>
</p>


Why is this post of mine not being accepted when i post it on my WhatsApp business channel

A simple local Math Solver built with Flask + SymPy.
Features:
- Algebra: solve equations, symbolically simplify
- Calculus: differentiate and integrate
- Numeric evaluation
- Clean frontend interface

Run locally
-----------

1. Create a virtual environment (recommended)
   python3 -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate

2. Install dependencies
   pip install -r requirements.txt

3. Run the app
   python app.py

4. Open browser:
   http://127.0.0.1:5000

Packaging into ZIP
------------------
From the parent folder run (Linux / macOS):
   zip -r math-solver.zip math-solver/

Windows (PowerShell):
   Compress-Archive -Path .\math-solver\* -DestinationPath math-solver.zip

Security note
-------------
- This project is for local testing and learning. Do not expose the Flask dev server directly to the public without proper security (use gunicorn + reverse proxy).
- Do not execute untrusted inputs on remote servers.

Developer Note📝
----------------
<p align="center">
  <img src="https://files.catbox.moe/ns8sy6.jpg" width="400"/>
</p>

# ❗❗AM A GOOD PERSON, TILL YOU SHOW ME A REASON NOT TO BE💀
