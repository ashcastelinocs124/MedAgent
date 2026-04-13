"""Demo web UI for the agentic healthcare search pipeline.

Run with:
    uvicorn src.app:app --reload

Then open http://localhost:8000
"""
from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import asynccontextmanager

import psycopg2
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from openai import OpenAI

from src.agents.context import PipelineResult
from src.personalization.base_graph import build_base_graph
from src.personalization.condition_registry import (
    CONDITION_CHECKLIST,
    match_freetext_conditions,
    resolve_conditions,
    resolve_medications,
)
from src.personalization.llm_augmenter import apply_answers, review_profile
from src.personalization.models import Condition, HealthLiteracy, Sex, UserProfile
from src.personalization.query_merge import QueryGraphMerger
from src.personalization.user_graph import UserSubgraphBuilder
from src.pipeline import Pipeline

load_dotenv()

_pipeline: Pipeline | None = None
_sessions: dict[str, dict] = {}
_openai_client: OpenAI | None = None
_builder: UserSubgraphBuilder | None = None
_merger: QueryGraphMerger | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline, _openai_client, _builder, _merger
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    _pipeline = Pipeline(conn, openai_client, anthropic_client, build_centroids=True, memory_dir="users")
    _openai_client = openai_client
    base_graph = build_base_graph()
    _builder = UserSubgraphBuilder(base_graph)
    _merger = QueryGraphMerger(base_graph)
    yield
    conn.close()


app = FastAPI(lifespan=lifespan)

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedAgent — Healthcare Search Demo</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 32px 16px; }
  .container { max-width: 800px; margin: 0 auto; }
  h1 { font-size: 1.6rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }
  .subtitle { color: #64748b; font-size: 0.875rem; margin-bottom: 28px; }
  .card { background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
  label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; font-weight: 500; }
  input, select, textarea {
    width: 100%; background: #0f172a; border: 1px solid #334155; border-radius: 8px;
    color: #e2e8f0; padding: 10px 14px; font-size: 0.95rem; outline: none;
    transition: border-color 0.15s;
  }
  input:focus, select:focus, textarea:focus { border-color: #6366f1; }
  textarea { resize: vertical; min-height: 80px; font-family: inherit; }
  .row { display: flex; gap: 16px; flex-wrap: wrap; }
  .col { flex: 1; min-width: 140px; }
  button {
    width: 100%; margin-top: 20px; padding: 12px; background: #6366f1; color: white;
    border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer;
    transition: background 0.15s;
  }
  button:hover { background: #4f46e5; }
  button:disabled { background: #334155; color: #64748b; cursor: not-allowed; }
  .spinner { display: none; text-align: center; color: #64748b; padding: 24px; }
  .badge {
    display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.75rem;
    font-weight: 600; margin-right: 6px; margin-bottom: 4px;
  }
  .badge-a { background: #14532d; color: #4ade80; }
  .badge-b { background: #1e3a5f; color: #60a5fa; }
  .badge-c { background: #3b1d6e; color: #c084fc; }
  .badge-d { background: #7c2d12; color: #fb923c; }
  .badge-tier-a { background: #14532d; color: #4ade80; }
  .badge-tier-b { background: #1e3a5f; color: #60a5fa; }
  .badge-tier-c { background: #78350f; color: #fbbf24; }
  .badge-tier-d { background: #450a0a; color: #f87171; }
  .step { border-left: 3px solid #334155; padding-left: 16px; margin-bottom: 20px; }
  .step-label { font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase;
                letter-spacing: 0.05em; margin-bottom: 6px; }
  .step-value { font-size: 0.9rem; color: #cbd5e1; }
  .answer { font-size: 1rem; line-height: 1.7; color: #e2e8f0; }
  .answer h1, .answer h2 { font-size: 1.1rem; font-weight: 700; color: #f1f5f9; margin: 16px 0 8px; }
  .answer h3 { font-size: 1rem; font-weight: 600; color: #cbd5e1; margin: 12px 0 6px; }
  .answer ul, .answer ol { padding-left: 20px; margin: 8px 0; }
  .answer li { margin-bottom: 4px; }
  .answer strong { color: #f1f5f9; }
  .answer p { margin: 8px 0; }
  .answer table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.875rem; }
  .answer th, .answer td { border: 1px solid #334155; padding: 6px 10px; text-align: left; }
  .answer th { background: #1e293b; color: #94a3b8; }
  .confidence-bar { height: 6px; border-radius: 3px; background: #1e293b; margin-top: 8px; overflow: hidden; }
  .confidence-fill { height: 100%; border-radius: 3px; transition: width 0.4s; }
  .citation { background: #0f172a; border-radius: 8px; padding: 12px; margin-top: 8px;
              font-size: 0.82rem; color: #94a3b8; }
  .disclaimer { background: #2d1b00; border: 1px solid #92400e; border-radius: 8px;
                padding: 12px 16px; color: #fbbf24; font-size: 0.875rem; margin-top: 16px; }
  .flag { background: #450a0a; color: #f87171; border-radius: 4px; padding: 2px 8px;
          font-size: 0.75rem; font-weight: 600; margin-right: 4px; }
  .error { background: #450a0a; border: 1px solid #991b1b; border-radius: 8px;
           padding: 16px; color: #f87171; }
  #result { display: none; }
</style>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
<div class="container">
  <h1>MedAgent — Healthcare Search</h1>
  <p class="subtitle">Agentic pipeline demo · Four-agent query processing · Hybrid search (pgvector + Postgres FTS)</p>

  <div id="profile-banner" style="display:none;margin-bottom:20px;"></div>

  <div class="card">
    <div style="margin-bottom:16px;">
      <label>Your health question</label>
      <textarea id="query" placeholder="e.g. What is metformin used for? What are symptoms of high blood pressure?"></textarea>
    </div>
    <div class="row">
      <div class="col">
        <label>Age</label>
        <input type="number" id="age" value="40" min="1" max="120">
      </div>
      <div class="col">
        <label>Sex</label>
        <select id="sex">
          <option value="male">Male</option>
          <option value="female">Female</option>
        </select>
      </div>
      <div class="col">
        <label>Health literacy</label>
        <select id="literacy">
          <option value="low">Low (plain language)</option>
          <option value="medium" selected>Medium</option>
          <option value="high">High (clinical)</option>
        </select>
      </div>
    </div>
    <button id="submit-btn" onclick="runQuery()">Run Pipeline</button>
  </div>

  <div class="spinner" id="spinner">Running four-agent pipeline… this takes ~30–60 seconds</div>

  <div id="result">
    <div class="card">
      <div style="font-size:0.7rem;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:14px;">
        Pipeline Steps
      </div>

      <div class="step">
        <div class="step-label"><span class="badge badge-a">A</span> Query Understanding</div>
        <div class="step-value">
          Category: <strong id="r-category">—</strong> &nbsp;·&nbsp;
          Method: <strong id="r-method">—</strong>
          <div style="margin-top:6px;font-size:0.8rem;color:#64748b;">Terms: <span id="r-terms">—</span></div>
        </div>
      </div>

      <div class="step">
        <div class="step-label"><span class="badge badge-b">B</span> Retrieval Planning</div>
        <div class="step-value" id="r-retrieval">Brain context loaded, retrieval plan built.</div>
      </div>

      <div class="step">
        <div class="step-label"><span class="badge badge-c">C</span> Evidence Synthesis</div>
        <div class="step-value"><span id="r-citation-count">—</span> sources retrieved · Claude claude-sonnet-4-6 synthesized response</div>
      </div>

      <div class="step">
        <div class="step-label"><span class="badge badge-d">D</span> Verification</div>
        <div class="step-value">
          Confidence: <strong id="r-confidence-pct">—</strong>
          <div class="confidence-bar"><div class="confidence-fill" id="r-confidence-bar"></div></div>
          <div style="margin-top:6px;" id="r-flags"></div>
        </div>
      </div>
    </div>

    <div class="card">
      <div style="font-size:0.7rem;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:14px;">
        Answer
      </div>
      <div class="answer" id="r-answer"></div>
      <div class="disclaimer" id="r-disclaimer" style="display:none;"></div>
    </div>

    <div class="card" id="citations-card">
      <div style="font-size:0.7rem;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;">
        Citations
      </div>
      <div id="r-citations"></div>
    </div>
  </div>
</div>

<script>
// Read session_id from URL query params
const _urlParams = new URLSearchParams(window.location.search);
const _sessionId = _urlParams.get('session_id');

// Show profile banner
(function() {
  const banner = document.getElementById('profile-banner');
  if (_sessionId) {
    banner.style.display = 'block';
    banner.innerHTML = '<div style="background:#14532d;border:1px solid #22c55e;border-radius:8px;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;">'
      + '<span style="color:#4ade80;font-size:0.875rem;font-weight:600;">Profile active — personalized results enabled</span>'
      + '<a href="/onboarding" style="color:#6366f1;font-size:0.8rem;text-decoration:underline;">Update profile</a>'
      + '</div>';
  } else {
    banner.style.display = 'block';
    banner.innerHTML = '<div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:10px 16px;">'
      + '<a href="/onboarding" style="color:#6366f1;font-size:0.875rem;font-weight:500;text-decoration:none;">'
      + 'Set up your profile for personalized results &rarr;</a></div>';
  }
})();

async function runQuery() {
  const query = document.getElementById('query').value.trim();
  if (!query) { alert('Please enter a question.'); return; }

  document.getElementById('submit-btn').disabled = true;
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('result').style.display = 'none';

  try {
    const payload = {
      query,
      age: parseInt(document.getElementById('age').value) || 40,
      sex: document.getElementById('sex').value,
      literacy: document.getElementById('literacy').value,
    };
    if (_sessionId) { payload.session_id = _sessionId; }

    const resp = await fetch('/query', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await resp.json();
    if (data.error) { alert('Error: ' + data.error); return; }

    // Agent A
    document.getElementById('r-category').textContent = data.category || '—';
    document.getElementById('r-method').textContent = data.classification_method || '—';
    document.getElementById('r-terms').textContent = (data.normalized_terms || []).join(', ') || '—';

    // Agent C
    document.getElementById('r-citation-count').textContent = (data.citations || []).length;

    // Agent D — confidence
    const pct = Math.round((data.confidence || 0) * 100);
    document.getElementById('r-confidence-pct').textContent = pct + '%';
    const bar = document.getElementById('r-confidence-bar');
    bar.style.width = pct + '%';
    bar.style.background = pct >= 80 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';

    // Flags
    const flagsEl = document.getElementById('r-flags');
    flagsEl.innerHTML = (data.uncertainty_flags || []).map(f => `<span class="flag">${f}</span>`).join('');

    // Answer — strip residual inline citation tags, then render markdown
    const rawAnswer = (data.answer_text || '').replace(/\[TIER_[A-D]:\s*\w+\]/g, '').trim();
    document.getElementById('r-answer').innerHTML = marked.parse(rawAnswer);

    // Disclaimer
    const discEl = document.getElementById('r-disclaimer');
    if (data.disclaimer) {
      discEl.textContent = '⚠ ' + data.disclaimer;
      discEl.style.display = 'block';
    } else {
      discEl.style.display = 'none';
    }

    // Citations
    const citEl = document.getElementById('r-citations');
    citEl.innerHTML = (data.citations || []).map(c => {
      const tierClass = 'badge-tier-' + c.quality_tier.toLowerCase().replace('tier_', '');
      const simPct = Math.round((c.relevance_score || 0) * 100);
      const simColor = simPct >= 65 ? '#22c55e' : simPct >= 45 ? '#f59e0b' : '#ef4444';
      return `<div class="citation">
        <span class="badge ${tierClass}">${c.quality_tier}</span>
        <strong>${c.source_table}</strong> · ID ${c.record_id}
        <span style="float:right;font-size:0.75rem;color:${simColor};font-weight:600;">sim ${simPct}%</span><br>
        <span style="color:#64748b;">${c.text_snippet}</span>
      </div>`;
    }).join('');

    document.getElementById('result').style.display = 'block';
  } catch (e) {
    alert('Request failed: ' + e.message);
  } finally {
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('spinner').style.display = 'none';
  }
}
</script>
</body>
</html>"""

# ── Onboarding Wizard HTML ──────────────────────────────────────────────────

_ONBOARDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedAgent — Profile Setup</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 32px 16px; }
  .container { max-width: 800px; margin: 0 auto; }
  h1 { font-size: 1.6rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }
  .subtitle { color: #64748b; font-size: 0.875rem; margin-bottom: 28px; }
  .card { background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
  label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; font-weight: 500; }
  input, select, textarea {
    width: 100%; background: #0f172a; border: 1px solid #334155; border-radius: 8px;
    color: #e2e8f0; padding: 10px 14px; font-size: 0.95rem; outline: none;
    transition: border-color 0.15s;
  }
  input:focus, select:focus, textarea:focus { border-color: #6366f1; }
  textarea { resize: vertical; min-height: 80px; font-family: inherit; }
  .row { display: flex; gap: 16px; flex-wrap: wrap; }
  .col { flex: 1; min-width: 140px; }
  button, .btn {
    display: inline-block; padding: 12px 24px; background: #6366f1; color: white;
    border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer;
    transition: background 0.15s; text-align: center;
  }
  button:hover, .btn:hover { background: #4f46e5; }
  button:disabled, .btn:disabled { background: #334155; color: #64748b; cursor: not-allowed; }
  .btn-secondary { background: #334155; color: #94a3b8; }
  .btn-secondary:hover { background: #475569; color: #e2e8f0; }
  .btn-row { display: flex; gap: 12px; margin-top: 24px; }
  .btn-row .btn-secondary { flex: 0 0 auto; }
  .btn-row button:last-child, .btn-row .btn:last-child { flex: 1; }

  /* Step indicator */
  .step-indicator { display: flex; gap: 8px; margin-bottom: 24px; align-items: center; }
  .step-dot {
    width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-size: 0.8rem; font-weight: 700;
    background: #334155; color: #64748b; transition: all 0.2s;
  }
  .step-dot.active { background: #6366f1; color: #fff; }
  .step-dot.done { background: #14532d; color: #4ade80; }
  .step-line { flex: 1; height: 2px; background: #334155; }
  .step-line.done { background: #22c55e; }
  .step-label-text { font-size: 0.8rem; color: #64748b; margin-left: 8px; }

  /* Condition groups */
  .condition-group { margin-bottom: 20px; }
  .condition-group-title {
    font-size: 0.85rem; font-weight: 700; color: #94a3b8; margin-bottom: 10px;
    text-transform: uppercase; letter-spacing: 0.04em;
  }
  .condition-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px; }
  .condition-item {
    display: flex; align-items: center; gap: 8px; padding: 8px 12px;
    background: #0f172a; border: 1px solid #334155; border-radius: 8px;
    cursor: pointer; transition: border-color 0.15s, background 0.15s;
    font-size: 0.9rem;
  }
  .condition-item:hover { border-color: #6366f1; }
  .condition-item.selected { border-color: #6366f1; background: rgba(99,102,241,0.1); }
  .condition-item input[type="checkbox"] {
    width: 16px; height: 16px; accent-color: #6366f1; cursor: pointer;
    flex-shrink: 0; padding: 0;
  }
  .condition-item label { margin: 0; font-size: 0.9rem; color: #e2e8f0; cursor: pointer; }

  /* Summary list */
  .summary-section { margin-bottom: 16px; }
  .summary-section-title {
    font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; margin-bottom: 8px;
  }
  .summary-item { font-size: 0.9rem; color: #cbd5e1; padding: 4px 0; }
  .summary-tag {
    display: inline-block; padding: 4px 10px; background: #0f172a; border: 1px solid #334155;
    border-radius: 6px; font-size: 0.82rem; color: #e2e8f0; margin: 2px 4px 2px 0;
  }

  /* Spinner / status */
  .spinner-overlay {
    display: none; text-align: center; padding: 40px 24px;
  }
  .spinner-overlay .spinner-ring {
    display: inline-block; width: 40px; height: 40px; border: 3px solid #334155;
    border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spinner-overlay .spinner-text { color: #94a3b8; margin-top: 16px; font-size: 0.95rem; }

  /* Clarification */
  .clarify-card { background: #1e293b; border-radius: 12px; padding: 24px; margin-bottom: 16px; }
  .clarify-question { font-size: 1rem; color: #f1f5f9; margin-bottom: 14px; font-weight: 500; }
  .clarify-options { display: flex; flex-wrap: wrap; gap: 8px; }
  .clarify-btn {
    padding: 8px 18px; background: #0f172a; border: 1px solid #334155; border-radius: 8px;
    color: #e2e8f0; font-size: 0.9rem; cursor: pointer; transition: all 0.15s;
  }
  .clarify-btn:hover { border-color: #6366f1; background: rgba(99,102,241,0.1); }
  .clarify-btn.selected { border-color: #6366f1; background: rgba(99,102,241,0.15); color: #a5b4fc; font-weight: 600; }

  .error { background: #450a0a; border: 1px solid #991b1b; border-radius: 8px;
           padding: 16px; color: #f87171; }

  /* Wizard step panels */
  .wizard-step { display: none; }
  .wizard-step.active { display: block; }
</style>
</head>
<body>
<div class="container">
  <h1>MedAgent — Profile Setup</h1>
  <p class="subtitle">Tell us about yourself so we can personalize your search results</p>

  <!-- Step indicator -->
  <div class="step-indicator" id="step-indicator">
    <div class="step-dot active" id="dot-1">1</div>
    <div class="step-line" id="line-1"></div>
    <div class="step-dot" id="dot-2">2</div>
    <div class="step-line" id="line-2"></div>
    <div class="step-dot" id="dot-3">3</div>
    <div class="step-line" id="line-3"></div>
    <div class="step-dot" id="dot-4">4</div>
    <span class="step-label-text" id="step-label">Step 1 of 4 — Demographics</span>
  </div>

  <!-- Step 1: Demographics -->
  <div class="wizard-step active" id="step-1">
    <div class="card">
      <div class="row" style="margin-bottom:16px;">
        <div class="col">
          <label for="ob-age">Age</label>
          <input type="number" id="ob-age" value="" min="1" max="120" placeholder="e.g. 45">
        </div>
        <div class="col">
          <label for="ob-sex">Sex</label>
          <select id="ob-sex">
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
            <option value="prefer_not_to_say">Prefer not to say</option>
          </select>
        </div>
        <div class="col">
          <label for="ob-literacy">Health Literacy</label>
          <select id="ob-literacy">
            <option value="low">Low (plain language)</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High (clinical detail)</option>
          </select>
        </div>
      </div>
      <div class="btn-row">
        <button onclick="goStep(2)">Next</button>
      </div>
    </div>
  </div>

  <!-- Step 2: Conditions -->
  <div class="wizard-step" id="step-2">
    <div class="card" id="conditions-card">
      <div id="conditions-loading" style="text-align:center;color:#64748b;padding:20px;">
        Loading conditions...
      </div>
      <div id="conditions-list" style="display:none;"></div>
      <div style="margin-top:20px;">
        <label for="ob-freetext">Have any other conditions not listed above?</label>
        <textarea id="ob-freetext" placeholder="e.g. celiac disease, Raynaud's, fibromyalgia"></textarea>
      </div>
      <div class="btn-row">
        <button class="btn-secondary" onclick="goStep(1)">Back</button>
        <button onclick="goStep(3)">Next</button>
      </div>
    </div>
  </div>

  <!-- Step 3: Medications -->
  <div class="wizard-step" id="step-3">
    <div class="card">
      <div style="margin-bottom:16px;">
        <label for="ob-meds">Current medications (one per line)</label>
        <textarea id="ob-meds" style="min-height:120px;" placeholder="e.g. Metformin&#10;Lisinopril&#10;Ibuprofen"></textarea>
      </div>
      <div class="btn-row">
        <button class="btn-secondary" onclick="goStep(2)">Back</button>
        <button onclick="goStep(4)">Next</button>
      </div>
    </div>
  </div>

  <!-- Step 4: Summary + Confirm -->
  <div class="wizard-step" id="step-4">
    <div class="card" id="summary-card">
      <div class="summary-section">
        <div class="summary-section-title">Demographics</div>
        <div id="sum-demographics" class="summary-item"></div>
      </div>
      <div class="summary-section">
        <div class="summary-section-title">Conditions</div>
        <div id="sum-conditions" class="summary-item"></div>
      </div>
      <div class="summary-section">
        <div class="summary-section-title">Medications</div>
        <div id="sum-medications" class="summary-item"></div>
      </div>
      <div class="btn-row">
        <button class="btn-secondary" onclick="goStep(3)">Back</button>
        <button id="confirm-btn" onclick="confirmProfile()">Confirm Profile</button>
      </div>
    </div>

    <!-- Spinner while waiting for /profile/review -->
    <div class="spinner-overlay" id="review-spinner">
      <div class="spinner-ring"></div>
      <div class="spinner-text">Analyzing your profile...</div>
    </div>

    <!-- Clarification questions area -->
    <div id="clarify-area" style="display:none;"></div>

    <!-- Error display -->
    <div id="review-error" style="display:none;"></div>
  </div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let currentStep = 1;
let conditionsData = [];  // fetched from /conditions
const stepLabels = {
  1: 'Demographics',
  2: 'Conditions',
  3: 'Medications',
  4: 'Review & Confirm',
};

// ── Step navigation ────────────────────────────────────────────────────────
function goStep(n) {
  // Validate before advancing
  if (n > currentStep) {
    if (currentStep === 1) {
      const age = parseInt(document.getElementById('ob-age').value);
      if (!age || age < 1 || age > 120) {
        alert('Please enter a valid age (1-120).');
        return;
      }
    }
  }

  // If going to step 4, populate summary
  if (n === 4) { populateSummary(); }

  // Hide current, show target
  document.getElementById('step-' + currentStep).classList.remove('active');
  document.getElementById('step-' + n).classList.add('active');
  currentStep = n;
  updateIndicator();
}

function updateIndicator() {
  for (let i = 1; i <= 4; i++) {
    const dot = document.getElementById('dot-' + i);
    dot.classList.remove('active', 'done');
    if (i < currentStep) { dot.classList.add('done'); dot.textContent = '\\u2713'; }
    else if (i === currentStep) { dot.classList.add('active'); dot.textContent = i; }
    else { dot.textContent = i; }

    if (i < 4) {
      const line = document.getElementById('line-' + i);
      line.classList.toggle('done', i < currentStep);
    }
  }
  document.getElementById('step-label').textContent =
    'Step ' + currentStep + ' of 4 \\u2014 ' + stepLabels[currentStep];
}

// ── Fetch conditions on load ───────────────────────────────────────────────
async function loadConditions() {
  try {
    const resp = await fetch('/conditions');
    conditionsData = await resp.json();
    renderConditions();
  } catch (e) {
    document.getElementById('conditions-loading').textContent = 'Failed to load conditions.';
  }
}

function renderConditions() {
  // Group by the 'group' field
  const groups = {};
  conditionsData.forEach(c => {
    if (!groups[c.group]) { groups[c.group] = []; }
    groups[c.group].push(c);
  });

  const container = document.getElementById('conditions-list');
  container.innerHTML = '';

  Object.keys(groups).forEach(groupName => {
    const section = document.createElement('div');
    section.className = 'condition-group';

    const title = document.createElement('div');
    title.className = 'condition-group-title';
    title.textContent = groupName;
    section.appendChild(title);

    const grid = document.createElement('div');
    grid.className = 'condition-grid';

    groups[groupName].forEach(c => {
      const item = document.createElement('div');
      item.className = 'condition-item';
      item.dataset.key = c.key;
      item.innerHTML = '<input type="checkbox" id="cond-' + c.key + '" value="' + c.key + '">'
        + '<label for="cond-' + c.key + '">' + c.name + '</label>';

      item.addEventListener('click', function(e) {
        if (e.target.tagName === 'INPUT') {
          item.classList.toggle('selected', e.target.checked);
        } else {
          const cb = item.querySelector('input');
          cb.checked = !cb.checked;
          item.classList.toggle('selected', cb.checked);
        }
      });

      grid.appendChild(item);
    });

    section.appendChild(grid);
    container.appendChild(section);
  });

  document.getElementById('conditions-loading').style.display = 'none';
  container.style.display = 'block';
}

// ── Gather selected conditions ─────────────────────────────────────────────
function getSelectedConditions() {
  const checked = document.querySelectorAll('#conditions-list input[type="checkbox"]:checked');
  return Array.from(checked).map(cb => cb.value);
}

function getSelectedConditionNames() {
  const checked = document.querySelectorAll('#conditions-list input[type="checkbox"]:checked');
  return Array.from(checked).map(cb => {
    const item = conditionsData.find(c => c.key === cb.value);
    return item ? item.name : cb.value;
  });
}

function getMedications() {
  return document.getElementById('ob-meds').value
    .split('\\n')
    .map(s => s.trim())
    .filter(s => s.length > 0);
}

// ── Summary ────────────────────────────────────────────────────────────────
function populateSummary() {
  const age = document.getElementById('ob-age').value;
  const sex = document.getElementById('ob-sex');
  const sexText = sex.options[sex.selectedIndex].text;
  const lit = document.getElementById('ob-literacy');
  const litText = lit.options[lit.selectedIndex].text;
  document.getElementById('sum-demographics').textContent =
    'Age ' + age + '  \\u00b7  ' + sexText + '  \\u00b7  Literacy: ' + litText;

  // Conditions
  const condNames = getSelectedConditionNames();
  const freetext = document.getElementById('ob-freetext').value.trim();
  const condEl = document.getElementById('sum-conditions');
  if (condNames.length === 0 && !freetext) {
    condEl.innerHTML = '<span style="color:#64748b;">None selected</span>';
  } else {
    let html = condNames.map(n => '<span class="summary-tag">' + n + '</span>').join('');
    if (freetext) { html += '<span class="summary-tag" style="border-color:#6366f1;">' + freetext + '</span>'; }
    condEl.innerHTML = html;
  }

  // Medications
  const meds = getMedications();
  const medsEl = document.getElementById('sum-medications');
  if (meds.length === 0) {
    medsEl.innerHTML = '<span style="color:#64748b;">None entered</span>';
  } else {
    medsEl.innerHTML = meds.map(m => '<span class="summary-tag">' + m + '</span>').join('');
  }
}

// ── Confirm & Review ───────────────────────────────────────────────────────
async function confirmProfile() {
  const summaryCard = document.getElementById('summary-card');
  const spinner = document.getElementById('review-spinner');
  const clarifyArea = document.getElementById('clarify-area');
  const errorEl = document.getElementById('review-error');

  summaryCard.style.display = 'none';
  clarifyArea.style.display = 'none';
  errorEl.style.display = 'none';
  spinner.style.display = 'block';

  const payload = {
    age: parseInt(document.getElementById('ob-age').value) || null,
    sex: document.getElementById('ob-sex').value,
    health_literacy: document.getElementById('ob-literacy').value,
    conditions: getSelectedConditions(),
    freetext_conditions: document.getElementById('ob-freetext').value.trim(),
    medications: getMedications(),
  };

  try {
    const resp = await fetch('/profile/review', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    spinner.style.display = 'none';

    if (data.error) {
      errorEl.className = 'error';
      errorEl.textContent = 'Error: ' + data.error;
      errorEl.style.display = 'block';
      summaryCard.style.display = 'block';
      return;
    }

    if (data.status === 'needs_clarification') {
      handleClarification(data);
    } else if (data.status === 'ready') {
      window.location.href = '/?session_id=' + data.session_id;
    }
  } catch (e) {
    spinner.style.display = 'none';
    errorEl.className = 'error';
    errorEl.textContent = 'Request failed: ' + e.message;
    errorEl.style.display = 'block';
    summaryCard.style.display = 'block';
  }
}

// ── Clarification Flow ─────────────────────────────────────────────────────
let _clarifySessionId = null;
let _clarifyAnswers = [];
let _clarifyQuestions = [];

function handleClarification(data) {
  _clarifySessionId = data.session_id;
  _clarifyQuestions = data.questions || [];
  _clarifyAnswers = new Array(_clarifyQuestions.length).fill(null);

  const area = document.getElementById('clarify-area');
  area.innerHTML = '';

  _clarifyQuestions.forEach((q, idx) => {
    const card = document.createElement('div');
    card.className = 'clarify-card';

    const qEl = document.createElement('div');
    qEl.className = 'clarify-question';
    qEl.textContent = q.question;
    card.appendChild(qEl);

    const opts = document.createElement('div');
    opts.className = 'clarify-options';
    opts.id = 'clarify-opts-' + idx;

    (q.options || []).forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'clarify-btn';
      btn.textContent = opt;
      btn.addEventListener('click', function() {
        // Deselect siblings
        opts.querySelectorAll('.clarify-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        _clarifyAnswers[idx] = opt;
      });
      opts.appendChild(btn);
    });

    card.appendChild(opts);
    area.appendChild(card);
  });

  // Submit button
  const submitRow = document.createElement('div');
  submitRow.className = 'btn-row';
  submitRow.style.marginTop = '8px';

  const backBtn = document.createElement('button');
  backBtn.className = 'btn-secondary';
  backBtn.textContent = 'Back to Summary';
  backBtn.addEventListener('click', function() {
    area.style.display = 'none';
    document.getElementById('summary-card').style.display = 'block';
  });
  submitRow.appendChild(backBtn);

  const submitBtn = document.createElement('button');
  submitBtn.textContent = 'Submit Answers';
  submitBtn.id = 'clarify-submit';
  submitBtn.addEventListener('click', submitClarification);
  submitRow.appendChild(submitBtn);

  area.appendChild(submitRow);
  area.style.display = 'block';
}

async function submitClarification() {
  // Check all questions answered
  if (_clarifyAnswers.some(a => a === null)) {
    alert('Please answer all questions before continuing.');
    return;
  }

  const area = document.getElementById('clarify-area');
  const spinner = document.getElementById('review-spinner');
  const errorEl = document.getElementById('review-error');

  area.style.display = 'none';
  errorEl.style.display = 'none';
  spinner.querySelector('.spinner-text').textContent = 'Finalizing your profile...';
  spinner.style.display = 'block';

  try {
    const resp = await fetch('/profile/clarify', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id: _clarifySessionId,
        answers: _clarifyAnswers,
      }),
    });
    const data = await resp.json();
    spinner.style.display = 'none';

    if (data.error) {
      errorEl.className = 'error';
      errorEl.textContent = 'Error: ' + data.error;
      errorEl.style.display = 'block';
      area.style.display = 'block';
      return;
    }

    if (data.status === 'ready') {
      window.location.href = '/?session_id=' + _clarifySessionId;
    }
  } catch (e) {
    spinner.style.display = 'none';
    errorEl.className = 'error';
    errorEl.textContent = 'Request failed: ' + e.message;
    errorEl.style.display = 'block';
    area.style.display = 'block';
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
loadConditions();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return _HTML


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding():
    """Serve the 4-step profile onboarding wizard."""
    return _ONBOARDING_HTML


# ── Condition Checklist Endpoint ─────────────────────────────────────────────


@app.get("/conditions")
async def conditions():
    """Return the full condition checklist for the onboarding wizard."""
    return CONDITION_CHECKLIST


# ── Profile Review Endpoint ──────────────────────────────────────────────────


@app.post("/profile/review")
async def profile_review(body: dict):
    """Build a user profile, run the 5-stage pipeline, and LLM-review weights.

    Accepts checklist condition keys, free-text conditions, medications, and
    demographics.  Returns either ``"ready"`` with final weights or
    ``"needs_clarification"`` with follow-up questions.
    """
    if _openai_client is None or _builder is None or _merger is None:
        return JSONResponse({"error": "Not initialized"}, status_code=503)

    sex_map = {
        "male": Sex.MALE,
        "female": Sex.FEMALE,
        "other": Sex.OTHER,
        "prefer_not_to_say": Sex.PREFER_NOT_TO_SAY,
    }
    literacy_map = {
        "low": HealthLiteracy.LOW,
        "medium": HealthLiteracy.MEDIUM,
        "high": HealthLiteracy.HIGH,
    }

    # Parse conditions from checklist keys + free-text
    selected_keys = [c["key"] if isinstance(c, dict) else c for c in body.get("conditions", [])]
    conditions_list = resolve_conditions(selected_keys)
    freetext = body.get("freetext_conditions", "")
    if freetext:
        conditions_list.extend(match_freetext_conditions(freetext))
    medications = resolve_medications(body.get("medications", []))

    profile = UserProfile(
        age=body.get("age"),
        sex=sex_map.get(body.get("sex", "prefer_not_to_say"), Sex.PREFER_NOT_TO_SAY),
        health_literacy=literacy_map.get(
            body.get("health_literacy", "medium"), HealthLiteracy.MEDIUM
        ),
        conditions=conditions_list,
        medications=medications,
    )

    # Run the 5-stage personalization pipeline to get a user subgraph
    subgraph = _builder.build(profile)

    # Compute baseline weights across all categories.
    # Iterate over every category node and call plan_retrieval; keep the
    # maximum effective weight observed for each linked category.
    all_weights: dict[str, float] = {}
    for node in _merger.base_graph.nodes:
        if not node.startswith("cat:"):
            continue
        cat_id = node.replace("cat:", "")
        plan = _merger.plan_retrieval(cat_id, subgraph)
        for c, w in plan.effective_weights.items():
            all_weights[c] = max(all_weights.get(c, 0.0), w)

    # LLM review with GPT-4o
    try:
        review_result = await review_profile(_openai_client, profile, all_weights)
    except Exception:
        review_result = {}

    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = {
        "profile": profile,
        "baseline_weights": all_weights.copy(),
        "review_result": review_result,
    }

    if review_result.get("needs_clarification"):
        # Apply preliminary adjustments now; final adjustments after clarify
        prelim = review_result.get("_clamped_preliminary", {})
        final_weights = {**all_weights, **prelim}
        _sessions[session_id]["weights"] = final_weights

        return {
            "status": "needs_clarification",
            "questions": [
                {"question": q["question"], "options": q["options"]}
                for q in review_result.get("questions", [])
            ],
            "preliminary_weights": prelim,
            "session_id": session_id,
        }
    else:
        clamped = review_result.get("_clamped_adjustments", {})
        final_weights = {**all_weights, **clamped}
        _sessions[session_id]["weights"] = final_weights

        return {
            "status": "ready",
            "weights": final_weights,
            "adjustments_made": review_result.get("adjustments", {}),
            "session_id": session_id,
        }


# ── Profile Clarify Endpoint ─────────────────────────────────────────────────


@app.post("/profile/clarify")
async def profile_clarify(body: dict):
    """Apply user answers to clarifying questions and finalize weights.

    Expects ``session_id`` and ``answers`` (list of strings matching the
    question order from the review response).
    """
    session_id = body.get("session_id")
    session = _sessions.get(session_id) if session_id else None
    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    try:
        final_adjustments = await apply_answers(
            _openai_client,
            session["profile"],
            session["baseline_weights"],
            session["review_result"],
            body.get("answers", []),
        )
    except Exception:
        final_adjustments = {}

    # Merge: baseline + preliminary + final clarification adjustments
    weights = session.get("weights", session["baseline_weights"]).copy()
    weights.update(final_adjustments)
    session["weights"] = weights

    return {
        "status": "ready",
        "weights": weights,
        "adjustments_made": {
            cat: {
                "from": round(session["baseline_weights"].get(cat, 0.0), 3),
                "to": round(w, 3),
            }
            for cat, w in final_adjustments.items()
        },
    }


# ── Query Endpoint ───────────────────────────────────────────────────────────


@app.post("/query")
async def query(body: dict):
    if _pipeline is None:
        return JSONResponse({"error": "Pipeline not initialized"}, status_code=503)

    # Load session profile and weight overrides if a session_id is provided
    session_id = body.get("session_id")
    session = _sessions.get(session_id) if session_id else None
    weight_overrides = session["weights"] if session else None

    if session:
        profile = session["profile"]
    else:
        literacy_map = {
            "low": HealthLiteracy.LOW,
            "medium": HealthLiteracy.MEDIUM,
            "high": HealthLiteracy.HIGH,
        }
        sex_map = {"male": Sex.MALE, "female": Sex.FEMALE}
        profile = UserProfile(
            age=int(body.get("age", 40)),
            sex=sex_map.get(body.get("sex", "male"), Sex.MALE),
            health_literacy=literacy_map.get(
                body.get("literacy", "medium"), HealthLiteracy.MEDIUM
            ),
        )

    try:
        result: PipelineResult = await _pipeline.run(
            body["query"], profile, weight_overrides=weight_overrides,
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return {
        "answer_text": result.answer_text,
        "confidence": result.confidence,
        "disclaimer": result.disclaimer,
        "uncertainty_flags": result.uncertainty_flags,
        "category": result.category,
        "classification_method": result.debug.get("classification_method"),
        "normalized_terms": result.debug.get("normalized_terms", []),
        "debug": {
            "graph_must_load": result.debug.get("graph_must_load", []),
            "graph_may_load": result.debug.get("graph_may_load", []),
            "graph_effective_weights": result.debug.get("graph_effective_weights", {}),
            "search_results": result.debug.get("search_results_debug", []),
        },
        "citations": [
            {
                "record_id": c.record_id,
                "source_table": c.source_table,
                "quality_tier": c.quality_tier,
                "text_snippet": c.text_snippet,
                "relevance_score": round(c.relevance_score, 4),
            }
            for c in result.citations
        ],
    }
