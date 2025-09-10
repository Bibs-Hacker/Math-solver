async function postSolve(query){
  const resp = await fetch('/api/solve', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({query})
  });
  return resp.json();
}

const qEl = document.getElementById('query');
const solveBtn = document.getElementById('solveBtn');
const clearBtn = document.getElementById('clearBtn');
const resultBlock = document.getElementById('result');
const resultText = document.getElementById('resultText');

solveBtn.addEventListener('click', async ()=>{
  const q = qEl.value.trim();
  if(!q){ alert('Please type a math problem'); return; }
  solveBtn.disabled = true;
  solveBtn.textContent = 'Solving...';
  try{
    const res = await postSolve(q);
    if(res.ok){
      // Pretty formatting depends on returned structure
      let out = '';
      if(res.mode){
        out += `Mode: ${res.mode}\n\n`;
      }
      if(res.result){
        out += JSON.stringify(res.result, null, 2);
      } else {
        out += JSON.stringify(res, null, 2);
      }
      resultText.textContent = out;
    } else {
      resultText.textContent = (res.error || JSON.stringify(res));
    }
    resultBlock.classList.remove('hidden');
  }catch(err){
    resultText.textContent = 'Error: ' + err.message;
    resultBlock.classList.remove('hidden');
  }finally{
    solveBtn.disabled = false;
    solveBtn.textContent = 'Solve';
  }
});

clearBtn.addEventListener('click', ()=>{
  qEl.value = '';
  resultBlock.classList.add('hidden');
  resultText.textContent = '';
});
