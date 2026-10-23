// ===== TABS E NAVEGAÇÃO =====
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
    
    // Carrega os dados específicos de cada aba ao clicar
    if (btn.dataset.tab === 'ocorrencias') carregarSelectAlunos();
    if (btn.dataset.tab === 'turmas') carregarTurmasAdmin();
    if (btn.dataset.tab === 'mural') {
      carregarMural();
      carregarGraficos();
    }
  });
});

// ===== CADASTRAR ALUNO =====
document.getElementById('formAluno').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const form = e.target;
  const fd = new FormData(form);

  try {
    const r = await fetch('/api/alunos', { method: 'POST', body: fd });
    
    if (r.ok) {
      alert('✅ Aluno cadastrado com sucesso!');
      form.reset(); 
      
      const nomeArquivo = document.getElementById('nomeArquivo');
      if (nomeArquivo) nomeArquivo.innerText = '';

      if (typeof carregarTurmas === 'function') carregarTurmas();
    } else {
      const err = await r.json();
      alert('❌ Erro: ' + (err.erro || 'Falha ao cadastrar'));
    }
  } catch (error) {
    console.error(error);
    alert('❌ Erro de conexão com o servidor.');
  }
});

// ===== MOSTRAR NOME DA FOTO SELECIONADA =====
const inputFoto = document.getElementById('inputFoto');
const nomeArquivo = document.getElementById('nomeArquivo');

if (inputFoto) {
  inputFoto.addEventListener('change', function() {
    if (this.files && this.files.length > 0) {
      nomeArquivo.innerText = `✅ Arquivo selecionado: ${this.files[0].name}`;
    } else {
      nomeArquivo.innerText = "";
    }
  });
}

// ===== GERENCIAR TURMAS =====
async function carregarTurmasAdmin() {
  const r = await fetch('/api/turmas');
  const turmas = await r.json();
  const div = document.getElementById('listaTurmas');
  
  if (turmas.length === 0) {
    div.innerHTML = '<p style="color:#94a3b8;">Nenhuma turma cadastrada. Adicione a primeira acima!</p>';
    return;
  }

  div.innerHTML = turmas.map(t => `
    <div class="card-turma-admin">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <h3 style="margin:0; color:var(--marinho);">Turma ${t.nome}</h3>
        <button onclick="excluirTurma(${t.id})" style="background:none; border:none; color:#dc2626; cursor:pointer; font-size:20px; width:auto; padding:0;" title="Excluir turma">🗑</button>
      </div>
      
      <label>Turno</label>
      <select id="turno-${t.id}">
        <option value="Manhã" ${t.turno === 'Manhã' ? 'selected' : ''}>Manhã</option>
        <option value="Tarde" ${t.turno === 'Tarde' ? 'selected' : ''}>Tarde</option>
      </select>
      
      <label>Quantidade de Alunos</label>
      <input type="number" id="qtd-${t.id}" value="${t.qtd_alunos}" min="1">
      
      <button onclick="salvarTurma(${t.id})">Salvar Alterações</button>
    </div>
  `).join('');
}

async function cadastrarNovaTurma() {
  const nome = document.getElementById('novaTurmaNome').value;
  const turno = document.getElementById('novaTurmaTurno').value;
  const qtd = document.getElementById('novaTurmaQtd').value;

  if (!nome || !qtd) {
    alert('⚠️ Preencha o nome da turma e a quantidade de alunos.');
    return;
  }

  const r = await fetch('/api/turmas', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ nome, turno, qtd_alunos: parseInt(qtd) })
  });

  if (r.ok) {
    alert('✅ Turma criada com sucesso!');
    document.getElementById('novaTurmaNome').value = '';
    document.getElementById('novaTurmaQtd').value = '';
    carregarTurmasAdmin();
    carregarTurmas(); 
  } else {
    const err = await r.json();
    alert('❌ ' + (err.erro || 'Erro ao criar turma'));
  }
}

async function salvarTurma(id) {
  const turno = document.getElementById(`turno-${id}`).value;
  const qtd = document.getElementById(`qtd-${id}`).value;
  
  const r = await fetch(`/api/turmas/${id}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ turno, qtd_alunos: parseInt(qtd) })
  });
  if (r.ok) alert('✅ Turma atualizada com sucesso!');
}

async function excluirTurma(id) {
  if (!confirm('Tem certeza que deseja excluir esta turma?')) return;
  
  await fetch(`/api/turmas/${id}`, { method: 'DELETE' });
  carregarTurmasAdmin();
  carregarTurmas();
}

// ===== SISTEMA DE TURMAS E ALUNOS =====
let turmaAtual = "";

async function carregarTurmas() {
  const r = await fetch('/api/alunos');
  const alunos = await r.json();
  
  const turmasData = {};
  alunos.forEach(a => {
    if (!turmasData[a.turma]) turmasData[a.turma] = { qtd: 0, ocorrencias: 0 };
    turmasData[a.turma].qtd++;
    if (a.total_ocorrencias > 0) turmasData[a.turma].ocorrencias++;
  });

  const div = document.getElementById('viewTurmas');
  if (!div) return;
  
  if (Object.keys(turmasData).length === 0) {
    div.innerHTML = '<p style="color:#94a3b8;grid-column:1/-1;text-align:center;padding:40px;">Nenhum aluno cadastrado.</p>';
    return;
  }

  div.innerHTML = Object.keys(turmasData).sort().map(turma => {
    const data = turmasData[turma];
    const alertaGrave = data.ocorrencias > 0 ? `<div class="tag-grave">⚠️ ${data.ocorrencias} alertas</div>` : '';
    return `
      <div class="card-turma" onclick="abrirTurma('${turma}')">
        ${alertaGrave}
        <h2>${turma}</h2>
        <p>👥 ${data.qtd} alunos cadastrados</p>
        <p style="margin-top:10px; font-size:12px; opacity:0.8;">Clique para abrir</p>
      </div>
    `;
  }).join('');
}

function abrirTurma(turma) {
  turmaAtual = turma;
  document.getElementById('viewTurmas').style.display = 'none';
  document.getElementById('viewAlunos').style.display = 'block';
  document.getElementById('tituloTurmaAtual').innerText = `Turma ${turma}`;
  document.getElementById('busca').value = '';
  document.getElementById('filtroTurma').value = turma;
  document.getElementById('filtroTurno').value = '';
  carregarAlunos();
}

function voltarTurmas() {
  turmaAtual = "";
  document.getElementById('viewAlunos').style.display = 'none';
  document.getElementById('viewTurmas').style.display = 'grid';
  document.getElementById('filtroTurma').value = '';
  document.getElementById('busca').value = '';
  document.getElementById('filtroTurno').value = '';
  carregarTurmas();
}

async function carregarAlunos() {
  const busca = document.getElementById('busca')?.value || '';
  const turma = document.getElementById('filtroTurma')?.value || '';
  const turno = document.getElementById('filtroTurno')?.value || '';
  
  if (document.getElementById('viewAlunos').style.display !== 'none') {
    if (turma) document.getElementById('tituloTurmaAtual').innerText = `Turma ${turma}`;
    else if (turno) document.getElementById('tituloTurmaAtual').innerText = `Turno: ${turno}`;
    else document.getElementById('tituloTurmaAtual').innerText = `Todos os Alunos`;
  }

  const url = `/api/alunos?busca=${encodeURIComponent(busca)}&turma=${encodeURIComponent(turma)}&turno=${encodeURIComponent(turno)}`;
  const r = await fetch(url);
  const alunos = await r.json();
  
  const div = document.getElementById('listaAlunos');
  if (!alunos.length) {
    div.innerHTML = '<p style="color:#94a3b8;grid-column:1/-1;text-align:center;padding:40px;">Nenhum aluno encontrado.</p>';
    return;
  }
  
  div.innerHTML = alunos.map(a => {
    const foto = a.foto
      ? `<img class="aluno-foto" src="/uploads/${a.foto}">`
      : `<div class="aluno-foto vazia">${a.nome.charAt(0).toUpperCase()}</div>`;
    const badgeOcorrencia = a.total_ocorrencias > 0 
      ? `<div class="badge-ocorrencia">⚠️ ${a.total_ocorrencias}</div>`
      : `<div class="badge-ocorrencia ok">✓ 0</div>`;
    return `<div class="aluno-card" onclick="verAluno(${a.id},'${a.nome.replace(/'/g,"\\'")}')">
      ${badgeOcorrencia}
      ${foto}
      <div class="aluno-info">
        <h4>${a.nome}</h4>
        <p>${a.turno}</p>
        <span class="tag-turma">${a.turma}</span>
      </div>
    </div>`;
  }).join('');
}

carregarTurmas();

document.getElementById('busca')?.addEventListener('input', () => {
  if (turmaAtual === "" && document.getElementById('busca').value.length > 0) {
    document.getElementById('viewTurmas').style.display = 'none';
    document.getElementById('viewAlunos').style.display = 'block';
  }
  clearTimeout(window._t);
  window._t = setTimeout(carregarAlunos, 300);
});
document.getElementById('filtroTurma')?.addEventListener('change', (e) => {
  if (e.target.value && turmaAtual === "") {
    document.getElementById('viewTurmas').style.display = 'none';
    document.getElementById('viewAlunos').style.display = 'block';
  }
  carregarAlunos();
});
document.getElementById('filtroTurno')?.addEventListener('change', (e) => {
  if (e.target.value && turmaAtual === "") {
    document.getElementById('viewTurmas').style.display = 'none';
    document.getElementById('viewAlunos').style.display = 'block';
  }
  carregarAlunos();
});

// ===== BUSCA INTELIGENTE DE ALUNO NA ABA OCORRÊNCIAS =====
let todosAlunos = [];

async function carregarSelectAlunos() {
  const r = await fetch('/api/alunos');
  todosAlunos = await r.json();
}

const inputBuscaAluno = document.getElementById('buscaAlunoOcorrencia');
const listaSugestoes = document.getElementById('sugestoesAluno');
const inputHiddenAluno = document.getElementById('selAluno');

if (inputBuscaAluno) {
  inputBuscaAluno.addEventListener('input', (e) => {
    const valor = e.target.value.toLowerCase();
    inputHiddenAluno.value = ""; 
    
    if (valor.length === 0) {
      listaSugestoes.classList.remove('active');
      return;
    }

    const filtrados = todosAlunos.filter(a => a.nome.toLowerCase().includes(valor));
    
    if (filtrados.length === 0) {
      listaSugestoes.innerHTML = '<div class="autocomplete-item">Nenhum aluno encontrado</div>';
    } else {
      listaSugestoes.innerHTML = filtrados.slice(0, 10).map(a => 
        `<div class="autocomplete-item" onclick="selecionarAluno(${a.id}, '${a.nome.replace(/'/g,"\\'")}', '${a.turma}')">
          <strong>${a.nome}</strong> <span style="color:#94a3b8; font-size:12px;">(${a.turma})</span>
        </div>`
      ).join('');
    }
    listaSugestoes.classList.add('active');
  });

  document.addEventListener('click', (e) => {
    if (!inputBuscaAluno.contains(e.target) && !listaSugestoes.contains(e.target)) {
      listaSugestoes.classList.remove('active');
    }
  });
}

function selecionarAluno(id, nome, turma) {
  inputBuscaAluno.value = `${nome} (${turma})`;
  inputHiddenAluno.value = id;
  listaSugestoes.classList.remove('active');
}

// ===== REGISTRAR OCORRÊNCIA =====
document.getElementById('formOcorrencia').addEventListener('submit', async (e) => {
  e.preventDefault();
  const alunoId = document.getElementById('selAluno').value;
  
  if (!alunoId) {
    alert('⚠️ Por favor, busque e selecione um aluno na lista.');
    return;
  }

  const dataInput = document.getElementById('dataOcorrencia').value;
  const horaInput = document.getElementById('horaOcorrencia').value;

  let dataFormatada = "";
  if (dataInput) {
    const [ano, mes, dia] = dataInput.split('-');
    dataFormatada = `${dia}/${mes}/${ano}`;
  }

  const payload = {
    aluno_id: +alunoId,
    codigo: document.getElementById('selCodigo').value,
    descricao: document.getElementById('descricao').value,
    data: dataFormatada,
    hora: horaInput
  };
  
  try {
    const r = await fetch('/api/ocorrencias', {
      method: 'POST', 
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    
    if (r.ok) {
      alert('✅ Ocorrência registrada!');
      e.target.reset();
      
      inputBuscaAluno.value = "";
      inputHiddenAluno.value = "";
      
      const hoje = new Date();
      const ano = hoje.getFullYear();
      const mes = String(hoje.getMonth() + 1).padStart(2, '0');
      const dia = String(hoje.getDate()).padStart(2, '0');
      document.getElementById('dataOcorrencia').value = `${ano}-${mes}-${dia}`;

      carregarHistorico(payload.aluno_id);
      
      if (turmaAtual === "") carregarTurmas();
      else carregarAlunos();
      
      checarNotificacoes(); 
    } else {
      alert('❌ Erro ao registrar a ocorrência. Verifique os dados.');
    }
  } catch (error) {
    console.error(error);
    alert('❌ Erro de conexão com o servidor.');
  }
});

// ===== HISTÓRICO E MODAL =====
async function carregarHistorico(alunoId) {
  const r = await fetch(`/api/ocorrencias/${alunoId}`);
  const lista = await r.json();
  const div = document.getElementById('historico');
  if (!div) return;
  
  if (!lista.length) { div.innerHTML = '<p style="color:#94a3b8;">Nenhuma ocorrência registrada.</p>'; return; }
  
  div.innerHTML = lista.map(o => {
    const oc = OCORRENCIAS[o.codigo] || { nome: o.codigo, cor: '#64748b' };
    return `<div class="hist-item" style="border-left-color:${oc.cor}">
      <span class="badge" style="background:${oc.cor}">${o.codigo}</span>
      <strong>${oc.nome}</strong><br>
      <small>${o.registrado_por} • ${o.data}</small>
      ${o.descricao ? `<p style="margin-top:8px;font-size:13px;">${o.descricao}</p>` : ''}
    </div>`;
  }).join('');
}

async function verAluno(id, nome) {
  const modal = document.getElementById('modal');
  const body = document.getElementById('modalBody');
  body.innerHTML = `<h2>${nome}</h2><p style="color:#94a3b8;margin-bottom:15px;">Carregando...</p>`;
  modal.classList.add('active');
  
  const r = await fetch(`/api/ocorrencias/${id}`);
  const lista = await r.json();
  let html = `<h2>${nome}</h2>`;
  
  if (!lista.length) {
    html += '<p style="color:#94a3b8;margin:20px 0;">Nenhuma ocorrência registrada.</p>';
  } else {
    html += lista.map(o => {
      const oc = OCORRENCIAS[o.codigo] || { nome: o.codigo, cor: '#64748b' };
      return `<div class="hist-item" style="border-left-color:${oc.cor}; position: relative; padding-right: 40px;">
        <span class="badge" style="background:${oc.cor}">${o.codigo}</span>
        <strong>${oc.nome}</strong><br>
        <small>${o.registrado_por} • ${o.data}</small>
        ${o.descricao ? `<p style="margin-top:8px;font-size:13px;">${o.descricao}</p>` : ''}
        
        <!-- BOTÃO DE APAGAR A OCORRÊNCIA -->
        <button onclick="apagarOcorrencia(${o.id})" style="position: absolute; right: 10px; top: 10px; background: none; border: none; color: #dc2626; cursor: pointer; font-size: 18px;" title="Apagar Ocorrência">🗑</button>
      </div>`;
    }).join('');
  }
  
  html += `<div style="display: flex; gap: 10px; margin-top: 20px;">
    <a href="/aluno/${id}" style="flex: 1; text-align: center; text-decoration: none; background: var(--marinho); color: white; padding: 12px; border-radius: 8px; font-weight: 600; transition: transform 0.2s;">
      📄 Ver Ficha Completa
    </a>
    <button onclick="excluirAluno(${id})" 
      style="background:#dc2626;color:white;padding:12px 16px;
      border:none;border-radius:8px;cursor:pointer;font-weight:600;">🗑 Excluir Aluno</button>
  </div>`;
  body.innerHTML = html;
}

// FUNÇÃO PARA MANDAR A OCORRÊNCIA PARA A LIXEIRA
async function apagarOcorrencia(id) {
  if (!confirm("Tem certeza que deseja apagar esta ocorrência? Ela irá para a Lixeira.")) return;
  
  const r = await fetch(`/api/ocorrencias/${id}`, { method: 'DELETE' });
  if (r.ok) {
    alert('🗑 Ocorrência movida para a lixeira!');
    fecharModal();
    if (turmaAtual === "") carregarTurmas();
    else carregarAlunos();
  } else {
    alert('❌ Erro ao apagar ocorrência.');
  }
}

function fecharModal() { document.getElementById('modal').classList.remove('active'); }

async function excluirAluno(id) {
  if (!confirm('Tem certeza? Isso apaga o aluno e todas as ocorrências dele.')) return;
  await fetch(`/api/alunos/${id}`, { method: 'DELETE' });
  fecharModal();
  if (turmaAtual === "") carregarTurmas();
  else carregarAlunos();
}

// ===== MURAL GERAL E NOTIFICAÇÕES =====
let ultimaOcorrenciaVista = localStorage.getItem('ultimaOcorrencia') || 0;

async function carregarMural() {
  const turma = document.getElementById('filtroTurmaMural')?.value || '';
  const aluno = document.getElementById('filtroAlunoMural')?.value || '';
  const data = document.getElementById('filtroData')?.value || '';

  const url = `/api/todas_ocorrencias?turma=${turma}&aluno=${aluno}&data_ini=${data}`;
  const r = await fetch(url);
  const lista = await r.json();
  
  const div = document.getElementById('listaMural');
  if (!lista.length) {
    div.innerHTML = '<p style="color:#94a3b8;">Nenhuma ocorrência encontrada com esses filtros.</p>';
    return;
  }

  div.innerHTML = lista.map(o => {
    const oc = OCORRENCIAS[o.codigo] || { nome: o.codigo, cor: '#64748b' };
    return `
      <div class="hist-item" style="border-left-color:${oc.cor}">
        <div style="display: flex; justify-content: space-between;">
          <strong>${o.aluno_nome} (${o.aluno_turma})</strong>
          <small>${o.data}</small>
        </div>
        <span class="badge" style="background:${oc.cor}">${o.codigo}</span> ${oc.nome}<br>
        <small>Registrado por: ${o.registrado_por}</small>
        ${o.descricao ? `<p style="margin-top:8px; font-size:13px;">${o.descricao}</p>` : ''}
      </div>
    `;
  }).join('');
  
  if (lista.length > 0) {
    localStorage.setItem('ultimaOcorrencia', lista[0].id);
    document.getElementById('badge-notif').style.display = 'none';
  }
}

function filtrarMural() {
  carregarMural();
}

async function checarNotificacoes() {
  try {
    const r = await fetch('/api/todas_ocorrencias');
    const lista = await r.json();
    const novas = lista.filter(o => o.id > ultimaOcorrenciaVista).length;
    const badge = document.getElementById('badge-notif');
    if (novas > 0 && badge) {
      badge.innerText = novas;
      badge.style.display = 'block';
    }
  } catch (e) {}
}

function verNotificacoes() {
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const btnMural = document.querySelector('[data-tab="mural"]');
  if (btnMural) btnMural.classList.add('active');
  document.getElementById('mural').classList.add('active');
  carregarMural();
}

// ===== GRÁFICOS DO DASHBOARD =====
let chartTurmasInstance = null;
let chartCodigosInstance = null;

async function carregarGraficos() {
  try {
    const r = await fetch('/api/estatisticas');
    const dados = await r.json();
    
    if (chartTurmasInstance) chartTurmasInstance.destroy();
    if (chartCodigosInstance) chartCodigosInstance.destroy();

    const labelsTurmas = dados.turmas.map(t => `Turma ${t.turma}`);
    const dataTurmas = dados.turmas.map(t => t.total);
    
    const ctxTurmas = document.getElementById('graficoTurmas').getContext('2d');
    chartTurmasInstance = new Chart(ctxTurmas, {
      type: 'bar',
      data: {
        labels: labelsTurmas,
        datasets: [{
          label: 'Qtd. de Ocorrências',
          data: dataTurmas,
          backgroundColor: '#f97316',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
      }
    });

    const labelsCodigos = dados.codigos.map(c => c.codigo);
    const coresCodigos = dados.codigos.map(c => OCORRENCIAS[c.codigo] ? OCORRENCIAS[c.codigo].cor : '#ccc');
    const dataCodigos = dados.codigos.map(c => c.total);

    const ctxCodigos = document.getElementById('graficoCodigos').getContext('2d');
    chartCodigosInstance = new Chart(ctxCodigos, {
      type: 'doughnut',
      data: {
        labels: labelsCodigos,
        datasets: [{
          data: dataCodigos,
          backgroundColor: coresCodigos,
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } } }
      }
    });

  } catch (e) {
    console.error("Erro ao carregar gráficos", e);
  }
}

// ===== BOTÃO SAIR E BLOQUEIO AO SAIR DA TELA =====
function sairDoSistema(event) {
  if (event) event.preventDefault();
  fetch('/logout').finally(() => {
    window.location.href = '/login'; 
  });
}

function forcarLogoutSilencioso() {
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/logout');
  } else {
    fetch('/logout', { method: 'GET', keepalive: true });
  }
}

document.addEventListener('visibilitychange', () => {
  if (document.hidden) forcarLogoutSilencioso();
});

window.addEventListener('blur', () => {
  forcarLogoutSilencioso();
});

window.addEventListener('pageshow', (event) => {
  if (event.persisted) {
    forcarLogoutSilencioso();
    window.location.href = '/login';
  }
});

// ===== FINALIZAR ANO LETIVO =====
async function abrirFinalizarAno() {
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById('finalizar').classList.add('active');
  
  const r = await fetch('/api/alunos');
  const alunos = await r.json();
  
  const div = document.getElementById('listaAprovacao');
  
  if (!alunos.length) {
    div.innerHTML = '<p style="color:#94a3b8;">Nenhum aluno cadastrado.</p>';
    return;
  }

  div.innerHTML = alunos.map(a => `
    <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
      <div>
        <strong>${a.nome}</strong> - Turma ${a.turma}
      </div>
      <label style="display: flex; align-items: center; gap: 8px; font-weight: bold; color: #059669; cursor: pointer;">
        <input type="checkbox" class="check-aprovado" value="${a.id}" checked style="width: 20px; height: 20px;"> Aprovado
      </label>
    </div>
  `).join('');
}

async function salvarProgressao() {
  const aprovados = Array.from(document.querySelectorAll('.check-aprovado:checked')).map(cb => +cb.value);
  
  if (aprovados.length === 0 && !confirm("Nenhum aluno foi marcado como aprovado. Tem certeza que quer continuar?")) return;
  if (!confirm("⚠️ Tem certeza? Isso vai mudar as turmas dos alunos aprovados e mover os do 3º ano para 'FORMADO'. Não pode ser desfeito!")) return;
  
  const r = await fetch('/api/finalizar_ano', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ aprovados })
  });
  
  if (r.ok) {
    alert('✅ Ano letivo finalizado com sucesso!');
    carregarTurmas(); 
    document.querySelector('[data-tab="turmas"]').click();
  }
}

// ===== LIXEIRA =====
async function abrirLixeira() {
  const r = await fetch('/api/lixeira');
  const lixeira = await r.json();
  
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById('mural').classList.add('active');
  
  const div = document.getElementById('listaMural');
  
  div.innerHTML = `<h3>🗑 Lixeira de Ocorrências</h3>
    <button onclick="limparLixeira()" style="background: #dc2626; color: white; padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; margin-bottom: 20px; font-weight: bold;">Esvaziar Lixeira</button>
  ` + (lixeira.length === 0 ? '<p style="color:#94a3b8;">A lixeira está vazia.</p>' : lixeira.map(o => `
    <div class="hist-item" style="border-left-color: #94a3b8; opacity: 0.7;">
      <strong>${o.aluno_nome}</strong> <br>
      <small>${o.data} - Código: ${o.codigo}</small>
      <button onclick="restaurarOcorrencia(${o.id})" style="margin-top: 10px; background: #059669; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Restaurar</button>
    </div>
  `).join(''));
}

async function restaurarOcorrencia(id) {
  await fetch(`/api/ocorrencias/${id}/restaurar`, { method: 'PUT' });
  abrirLixeira();
}

async function limparLixeira() {
  if(!confirm("Apagar permanentemente todas as ocorrências da lixeira?")) return;
  await fetch('/api/lixeira/limpar', { method: 'DELETE' });
  abrirLixeira();
}

// ===== INICIALIZAÇÃO DO SISTEMA =====
setInterval(checarNotificacoes, 30000);
checarNotificacoes();

const inputData = document.getElementById('dataOcorrencia');
if (inputData) {
  const hoje = new Date();
  const ano = hoje.getFullYear();
  const mes = String(hoje.getMonth() + 1).padStart(2, '0');
  const dia = String(hoje.getDate()).padStart(2, '0');
  inputData.value = `${ano}-${mes}-${dia}`;
}
