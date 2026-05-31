//  CONFIG 
// Replace these after running deploy.sh — values are printed in the output.
const CONFIG = {
  uploadBucket:  "docmind-uploads",          // S3 upload bucket name
  region:        "ap-south-1",               // Your AWS region
  apiBaseUrl:    "https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/prod",
};

// S3 presigned URL endpoint (from API Gateway)
const PRESIGN_URL = `${CONFIG.apiBaseUrl}/presign`;
const DOCS_URL    = `${CONFIG.apiBaseUrl}/documents`;

//  UPLOAD PAGE LOGIC 

const fileInput  = document.getElementById("fileInput");
const dropZone   = document.getElementById("dropZone");
const filePreview= document.getElementById("filePreview");
const fileName   = document.getElementById("fileName");
const clearBtn   = document.getElementById("clearBtn");
const submitBtn  = document.getElementById("submitBtn");
const statusBar  = document.getElementById("statusBar");
const statusText = document.getElementById("statusText");
const successBar = document.getElementById("successBar");
const errorBar   = document.getElementById("errorBar");

let selectedFile = null;

if (fileInput) {
  // File chosen via button
  fileInput.addEventListener("change", (e) => setFile(e.target.files[0]));

  // Drag & drop
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    setFile(e.dataTransfer.files[0]);
  });

  clearBtn.addEventListener("click", clearFile);

  submitBtn.addEventListener("click", uploadFile);
}

function setFile(file) {
  if (!file) return;
  const allowed = ["application/pdf", "image/jpeg", "image/png", "image/tiff"];
  if (!allowed.includes(file.type)) {
    showError("Unsupported file type. Please upload a PDF, JPG, PNG, or TIFF.");
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showError("File too large. Max size is 10 MB.");
    return;
  }
  selectedFile = file;
  fileName.textContent = file.name;
  filePreview.style.display = "flex";
  submitBtn.disabled = false;
  hideError();
}

function clearFile() {
  selectedFile = null;
  fileInput.value = "";
  filePreview.style.display = "none";
  submitBtn.disabled = true;
}

async function uploadFile() {
  if (!selectedFile) return;

  showStatus("Getting upload URL...");

  try {
    // 1. Get presigned S3 URL from API Gateway
    const presignRes = await fetch(`${PRESIGN_URL}?file_name=${encodeURIComponent(selectedFile.name)}&content_type=${encodeURIComponent(selectedFile.type)}`);
    if (!presignRes.ok) throw new Error("Failed to get upload URL");
    const { upload_url, doc_id } = await presignRes.json();

    // 2. PUT file directly to S3
    showStatus("Uploading to S3...");
    const uploadRes = await fetch(upload_url, {
      method: "PUT",
      body: selectedFile,
      headers: { "Content-Type": selectedFile.type },
    });
    if (!uploadRes.ok) throw new Error("S3 upload failed");

    // 3. Show success
    statusBar.style.display = "none";
    successBar.style.display = "flex";
    document.getElementById("resultLink").href = `results.html?doc_id=${doc_id}`;

  } catch (err) {
    statusBar.style.display = "none";
    showError(err.message || "Upload failed. Please try again.");
  }
}

function showStatus(msg) {
  statusText.textContent = msg;
  statusBar.style.display = "flex";
  successBar.style.display = "none";
  hideError();
  submitBtn.disabled = true;
}

function showError(msg) {
  errorBar.textContent = " " + msg;
  errorBar.style.display = "block";
  submitBtn.disabled = false;
}

function hideError() {
  errorBar.style.display = "none";
}

//  RESULTS PAGE LOGIC 

const docItems  = document.getElementById("docItems");
const tabs      = document.querySelectorAll(".tab");

if (docItems) {
  loadDocumentList();

  // Tab switching
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
    });
  });

  // Auto-load doc if URL has ?doc_id=
  const params = new URLSearchParams(window.location.search);
  const autoId = params.get("doc_id");
  if (autoId) {
    // Give list a moment to render then open the doc
    setTimeout(() => loadDocument(autoId), 800);
  }
}

async function loadDocumentList() {
  try {
    const res  = await fetch(DOCS_URL);
    const data = await res.json();
    const docs = data.documents || [];

    if (docs.length === 0) {
      docItems.innerHTML = `<p class="empty-list">No documents yet. <a href="index.html">Upload one →</a></p>`;
      return;
    }

    docItems.innerHTML = docs.map((d) => `
      <div class="doc-item" data-id="${d.doc_id}" onclick="loadDocument('${d.doc_id}')">
        <span class="doc-item-icon"></span>
        <div class="doc-item-info">
          <span class="doc-item-name">${d.file_name}</span>
          <span class="doc-item-date">${formatDate(d.uploaded_at)}</span>
        </div>
        <span class="doc-item-status ${d.status}">${d.status}</span>
      </div>
    `).join("");

  } catch (err) {
    docItems.innerHTML = `<p class="error-list">Failed to load documents.</p>`;
  }
}

async function loadDocument(docId) {
  // Highlight selected
  document.querySelectorAll(".doc-item").forEach((el) => el.classList.remove("selected"));
  const selected = document.querySelector(`.doc-item[data-id="${docId}"]`);
  if (selected) selected.classList.add("selected");

  document.getElementById("emptyState").style.display    = "none";
  document.getElementById("extractionContent").style.display = "block";
  document.getElementById("detailFileName").textContent  = "Loading...";

  try {
    const res  = await fetch(`${DOCS_URL}/${docId}`);
    const doc  = await res.json();

    // Header
    document.getElementById("detailFileName").textContent = doc.file_name;
    document.getElementById("detailStatus").textContent   = doc.status;
    document.getElementById("detailDate").textContent     = formatDate(doc.uploaded_at);

    // Raw text
    document.getElementById("rawTextOutput").textContent = doc.raw_text || "No text extracted.";

    // Key-Values
    const kvBody  = document.getElementById("kvBody");
    const kvEmpty = document.getElementById("kvEmpty");
    const kv      = doc.key_values || {};
    const kvKeys  = Object.keys(kv);
    if (kvKeys.length === 0) {
      kvBody.innerHTML = "";
      kvEmpty.style.display = "block";
    } else {
      kvEmpty.style.display = "none";
      kvBody.innerHTML = kvKeys.map((k) => `
        <tr><td>${k}</td><td>${kv[k] || "—"}</td></tr>
      `).join("");
    }

    // Tables
    const tablesOut  = document.getElementById("tablesOutput");
    const tablesEmpty= document.getElementById("tablesEmpty");
    const tables     = doc.tables || [];
    if (tables.length === 0) {
      tablesOut.innerHTML = "";
      tablesEmpty.style.display = "block";
    } else {
      tablesEmpty.style.display = "none";
      tablesOut.innerHTML = tables.map((rows, i) => `
        <h4>Table ${i + 1}</h4>
        <div class="table-scroll">
          <table class="extracted-table">
            ${rows.map((row, ri) => `
              <tr>${row.map((cell) => ri === 0 ? `<th>${cell}</th>` : `<td>${cell}</td>`).join("")}</tr>
            `).join("")}
          </table>
        </div>
      `).join("");
    }

  } catch (err) {
    document.getElementById("detailFileName").textContent = "Failed to load document.";
  }
}

function formatDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}
