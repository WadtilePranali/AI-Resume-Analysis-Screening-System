document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.getAttribute('data-tab');
            navTabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(targetId).classList.add('active');

            if (targetId === 'taxonomy-pane') {
                loadTaxonomy();
            }
        });
    });

    // Toast utility
    window.showToast = function(message, isError = false) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        if (isError) {
            toast.style.backgroundColor = '#991b1b';
        }
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 4000);
    };

    // Loader controls
    const loader = document.getElementById('loading-overlay');
    const loaderText = document.getElementById('loader-text');

    function showLoader(text = "Analyzing resume against target criteria...") {
        loaderText.textContent = text;
        loader.style.display = 'flex';
    }

    function hideLoader() {
        loader.style.display = 'none';
    }

    // Cache sample data
    let sampleData = null;
    async function fetchSamples() {
        try {
            const res = await fetch('/api/samples');
            sampleData = await res.json();
        } catch (e) {
            console.error("Failed to load sample data", e);
        }
    }
    fetchSamples();

    // Check system health
    async function checkHealth() {
        try {
            const res = await fetch('/api/health');
            const data = await res.json();
            const badge = document.getElementById('engine-status-badge');
            if (badge) {
                badge.textContent = data.ai_engine;
            }
        } catch (e) {
            console.error("Health check error", e);
        }
    }
    checkHealth();

    // ----------------------------------------------------
    // Tab 1: Single Candidate Audit Logic
    // ----------------------------------------------------
    const singleDropzone = document.getElementById('single-dropzone');
    const singleFileInput = document.getElementById('single-file-input');
    const singleFileBadge = document.getElementById('single-file-badge');
    const singleFileName = document.getElementById('single-file-name');
    const singleJdInput = document.getElementById('single-jd-input');
    const singleResumePaste = document.getElementById('single-resume-paste');
    const togglePasteBtn = document.getElementById('toggle-paste-btn');
    const pasteSection = document.getElementById('paste-section');
    const uploadSection = document.getElementById('upload-section');

    let currentSingleFile = null;

    if (togglePasteBtn) {
        togglePasteBtn.addEventListener('click', () => {
            if (pasteSection.style.display === 'none') {
                pasteSection.style.display = 'block';
                uploadSection.style.display = 'none';
                togglePasteBtn.textContent = 'Upload File Instead';
            } else {
                pasteSection.style.display = 'none';
                uploadSection.style.display = 'block';
                togglePasteBtn.textContent = 'Paste Text Instead';
            }
        });
    }

    // Drag and drop handlers
    if (singleDropzone) {
        singleDropzone.addEventListener('click', () => singleFileInput.click());
        singleDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            singleDropzone.classList.add('dragover');
        });
        singleDropzone.addEventListener('dragleave', () => singleDropzone.classList.remove('dragover'));
        singleDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            singleDropzone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleSingleFileSelect(e.dataTransfer.files[0]);
            }
        });
        singleFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleSingleFileSelect(e.target.files[0]);
            }
        });
    }

    function handleSingleFileSelect(file) {
        currentSingleFile = file;
        singleFileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        singleFileBadge.style.display = 'inline-flex';
    }

    // Sample population buttons
    const btnSampleDs = document.getElementById('btn-sample-ds');
    const btnSampleFsd = document.getElementById('btn-sample-fsd');
    const btnSampleRes = document.getElementById('btn-sample-res');

    if (btnSampleDs) {
        btnSampleDs.addEventListener('click', () => {
            if (sampleData && sampleData.job_descriptions.data_scientist) {
                singleJdInput.value = sampleData.job_descriptions.data_scientist.text;
                showToast("Loaded Data Scientist Job Description");
            }
        });
    }

    if (btnSampleFsd) {
        btnSampleFsd.addEventListener('click', () => {
            if (sampleData && sampleData.job_descriptions.full_stack_ai) {
                singleJdInput.value = sampleData.job_descriptions.full_stack_ai.text;
                showToast("Loaded Full Stack AI Engineer Job Description");
            }
        });
    }

    if (btnSampleRes) {
        btnSampleRes.addEventListener('click', () => {
            if (sampleData && sampleData.resumes.strong_candidate) {
                pasteSection.style.display = 'block';
                uploadSection.style.display = 'none';
                if (togglePasteBtn) togglePasteBtn.textContent = 'Upload File Instead';
                singleResumePaste.value = sampleData.resumes.strong_candidate.text;
                showToast("Loaded Sample Candidate Resume (Pranali Wadtile)");
            }
        });
    }

    // Run Single Audit
    const btnRunAudit = document.getElementById('btn-run-audit');
    if (btnRunAudit) {
        btnRunAudit.addEventListener('click', async () => {
            const jdText = singleJdInput.value.trim();
            if (jdText.length < 20) {
                showToast("Please enter a valid Job Description (minimum 20 characters).", true);
                return;
            }

            const isPasting = pasteSection.style.display !== 'none';
            showLoader("Screening candidate against criteria...");

            try {
                let response;
                if (isPasting) {
                    const resumeText = singleResumePaste.value.trim();
                    if (resumeText.length < 20) {
                        hideLoader();
                        showToast("Please paste a valid resume text (minimum 20 characters).", true);
                        return;
                    }
                    const formData = new FormData();
                    formData.append('resume_text', resumeText);
                    formData.append('job_description', jdText);

                    response = await fetch('/api/analyze/text', {
                        method: 'POST',
                        body: formData
                    });
                } else {
                    if (!currentSingleFile) {
                        hideLoader();
                        showToast("Please choose or drag a resume file (.pdf, .docx, .txt).", true);
                        return;
                    }
                    const formData = new FormData();
                    formData.append('resume_file', currentSingleFile);
                    formData.append('job_description', jdText);

                    response = await fetch('/api/analyze/upload', {
                        method: 'POST',
                        body: formData
                    });
                }

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || "Analysis request failed.");
                }

                const data = await response.json();
                renderSingleResult(data);
                showToast("Resume Audit Complete!");
            } catch (err) {
                console.error(err);
                showToast(err.message, true);
            } finally {
                hideLoader();
            }
        });
    }

    function renderSingleResult(data) {
        const resultContainer = document.getElementById('single-result-container');
        resultContainer.style.display = 'block';
        resultContainer.scrollIntoView({ behavior: 'smooth' });

        // Score & Verdict
        document.getElementById('res-overall-score').textContent = `${data.overall_match_score}%`;
        const verdictBadge = document.getElementById('res-verdict-badge');
        verdictBadge.textContent = data.verdict;
        verdictBadge.className = `badge badge-${data.verdict_badge}`;

        // Metrics breakdown
        document.getElementById('res-skill-score').textContent = `${data.score_breakdown.skill_score}%`;
        document.getElementById('res-semantic-score').textContent = `${data.score_breakdown.semantic_score}%`;
        document.getElementById('res-exp-score').textContent = `${data.score_breakdown.experience_score}%`;
        document.getElementById('res-ats-score').textContent = `${data.ats_score}/100`;

        // Candidate Profile extracted
        const c = data.resume_extracted.contact;
        document.getElementById('cand-name').textContent = c.name || "Candidate";
        document.getElementById('cand-email').textContent = c.email || "Not Detected";
        document.getElementById('cand-phone').textContent = c.phone || "Not Detected";
        document.getElementById('cand-exp').textContent = `${data.resume_extracted.experience_years} Years`;
        document.getElementById('cand-edu').textContent = data.resume_extracted.education_level || "Not Specified";

        // Social Links
        const linksContainer = document.getElementById('cand-links');
        linksContainer.innerHTML = '';
        if (c.linkedin) {
            const a = document.createElement('a');
            a.href = c.linkedin;
            a.target = '_blank';
            a.className = 'btn btn-secondary btn-sm';
            a.textContent = 'LinkedIn Profile';
            linksContainer.appendChild(a);
        }
        if (c.github) {
            const a = document.createElement('a');
            a.href = c.github;
            a.target = '_blank';
            a.className = 'btn btn-secondary btn-sm';
            a.textContent = 'GitHub Profile';
            linksContainer.appendChild(a);
        }

        // Skills Breakdown
        const matchedContainer = document.getElementById('tags-matched-skills');
        matchedContainer.innerHTML = '';
        if (data.matched_skills.length === 0) {
            matchedContainer.innerHTML = '<span class="text-muted" style="font-size:0.8rem">No direct skills matched.</span>';
        } else {
            data.matched_skills.forEach(s => {
                const tag = document.createElement('span');
                tag.className = 'skill-tag matched';
                tag.textContent = `✓ ${s}`;
                matchedContainer.appendChild(tag);
            });
        }

        const missingContainer = document.getElementById('tags-missing-skills');
        missingContainer.innerHTML = '';
        if (data.missing_skills.length === 0) {
            missingContainer.innerHTML = '<span class="text-muted" style="font-size:0.8rem">All required skills matched!</span>';
        } else {
            data.missing_skills.forEach(s => {
                const tag = document.createElement('span');
                tag.className = 'skill-tag missing';
                tag.textContent = `+ ${s}`;
                missingContainer.appendChild(tag);
            });
        }

        const additionalContainer = document.getElementById('tags-additional-skills');
        additionalContainer.innerHTML = '';
        if (data.additional_skills.length === 0) {
            additionalContainer.innerHTML = '<span class="text-muted" style="font-size:0.8rem">None</span>';
        } else {
            data.additional_skills.forEach(s => {
                const tag = document.createElement('span');
                tag.className = 'skill-tag additional';
                tag.textContent = s;
                additionalContainer.appendChild(tag);
            });
        }

        // ATS Checklist
        const atsContainer = document.getElementById('ats-checklist-container');
        atsContainer.innerHTML = '';
        data.ats_checks.forEach(item => {
            const row = document.createElement('div');
            row.className = 'ats-check-item';
            const iconClass = item.status === 'PASS' ? 'pass' : (item.status === 'WARNING' ? 'warning' : 'fail');
            const iconSymbol = item.status === 'PASS' ? '✓' : (item.status === 'WARNING' ? '!' : '✕');

            row.innerHTML = `
                <div class="ats-status-icon ${iconClass}">${iconSymbol}</div>
                <div class="ats-check-content">
                    <div class="ats-check-header">
                        <span class="ats-check-title">${item.check}</span>
                        <span class="badge badge-${iconClass === 'pass' ? 'success' : (iconClass === 'warning' ? 'warning' : 'danger')}">${item.status}</span>
                    </div>
                    <div class="ats-check-msg">${item.message}</div>
                </div>
            `;
            atsContainer.appendChild(row);
        });

        // Recommendations
        const recList = document.getElementById('recommendations-list');
        recList.innerHTML = '';
        data.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.className = 'rec-item';
            li.innerHTML = `<span>💡</span><div>${rec}</div>`;
            recList.appendChild(li);
        });

        // Technical Interview Prep Questions
        const qList = document.getElementById('questions-list');
        qList.innerHTML = '';
        data.interview_questions.forEach((q, idx) => {
            const li = document.createElement('li');
            li.className = 'rec-item';
            li.style.borderLeftColor = '#10b981';
            li.innerHTML = `<span><strong>Q${idx + 1}:</strong></span><div>${q}</div>`;
            qList.appendChild(li);
        });
    }

    // ----------------------------------------------------
    // Tab 2: Recruiter Batch Screening Logic
    // ----------------------------------------------------
    const batchDropzone = document.getElementById('batch-dropzone');
    const batchFileInput = document.getElementById('batch-file-input');
    const batchFilesList = document.getElementById('batch-files-list');
    const batchJdInput = document.getElementById('batch-jd-input');
    const btnSampleBatch = document.getElementById('btn-sample-batch');
    const btnRunBatch = document.getElementById('btn-run-batch');
    const btnExportCsv = document.getElementById('btn-export-csv');

    let batchFiles = [];
    let lastBatchResults = null;

    if (batchDropzone) {
        batchDropzone.addEventListener('click', () => batchFileInput.click());
        batchDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            batchDropzone.classList.add('dragover');
        });
        batchDropzone.addEventListener('dragleave', () => batchDropzone.classList.remove('dragover'));
        batchDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            batchDropzone.classList.remove('dragover');
            handleBatchFilesSelect(e.dataTransfer.files);
        });
        batchFileInput.addEventListener('change', (e) => {
            handleBatchFilesSelect(e.target.files);
        });
    }

    function handleBatchFilesSelect(files) {
        for (let i = 0; i < files.length; i++) {
            batchFiles.push(files[i]);
        }
        updateBatchFilesUI();
    }

    function updateBatchFilesUI() {
        batchFilesList.innerHTML = '';
        if (batchFiles.length === 0) {
            batchFilesList.innerHTML = '<span class="text-muted" style="font-size:0.8rem">No files selected.</span>';
            return;
        }
        batchFiles.forEach((file, index) => {
            const pill = document.createElement('span');
            pill.className = 'file-selected-badge';
            pill.innerHTML = `📄 ${file.name} <button type="button" style="border:none;background:none;cursor:pointer;color:#dc2626;font-weight:bold" data-index="${index}">×</button>`;
            pill.querySelector('button').addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = parseInt(e.target.getAttribute('data-index'));
                batchFiles.splice(idx, 1);
                updateBatchFilesUI();
            });
            batchFilesList.appendChild(pill);
        });
    }

    // 1-Click Sample Batch
    if (btnSampleBatch) {
        btnSampleBatch.addEventListener('click', async () => {
            showLoader("Processing 3 sample candidates against Data Scientist criteria...");
            try {
                const response = await fetch('/api/screen-batch/sample', { method: 'POST' });
                if (!response.ok) throw new Error("Sample batch processing failed.");
                const data = await response.json();
                lastBatchResults = data;
                renderBatchResults(data);
                showToast("Sample Batch Processed Successfully!");
            } catch (err) {
                console.error(err);
                showToast(err.message, true);
            } finally {
                hideLoader();
            }
        });
    }

    // Run Custom Batch
    if (btnRunBatch) {
        btnRunBatch.addEventListener('click', async () => {
            const jdText = batchJdInput.value.trim();
            if (jdText.length < 20) {
                showToast("Please provide a target Job Description for batch screening.", true);
                return;
            }
            if (batchFiles.length === 0) {
                showToast("Please select at least 1 resume file to screen.", true);
                return;
            }

            showLoader(`Screening ${batchFiles.length} resumes...`);
            try {
                const formData = new FormData();
                formData.append('job_description', jdText);
                batchFiles.forEach(f => {
                    formData.append('resumes', f);
                });

                const response = await fetch('/api/screen-batch', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.detail || "Batch screening request failed.");
                }

                const data = await response.json();
                lastBatchResults = data;
                renderBatchResults(data);
                showToast(`Screening complete for ${data.processed_count} candidates!`);
            } catch (err) {
                console.error(err);
                showToast(err.message, true);
            } finally {
                hideLoader();
            }
        });
    }

    function renderBatchResults(data) {
        const batchResultsSection = document.getElementById('batch-results-section');
        batchResultsSection.style.display = 'block';
        batchResultsSection.scrollIntoView({ behavior: 'smooth' });

        document.getElementById('batch-job-title').textContent = data.job_title;
        document.getElementById('batch-count-total').textContent = data.processed_count;
        document.getElementById('batch-time').textContent = `${data.processing_time_seconds}s`;

        // Render Missing Skills Across Pool
        const poolSkillsContainer = document.getElementById('pool-missing-skills');
        poolSkillsContainer.innerHTML = '';
        if (data.top_missing_skills_across_pool && data.top_missing_skills_across_pool.length > 0) {
            data.top_missing_skills_across_pool.forEach(item => {
                const badge = document.createElement('span');
                badge.className = 'skill-tag missing';
                badge.textContent = `${item.skill} (missing in ${item.missing_in_candidates_count} candidates)`;
                poolSkillsContainer.appendChild(badge);
            });
        } else {
            poolSkillsContainer.innerHTML = '<span class="text-muted" style="font-size:0.8rem">No common missing skills detected.</span>';
        }

        // Render Table Rows
        const tbody = document.getElementById('batch-table-body');
        tbody.innerHTML = '';

        data.candidates.forEach(cand => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>#${cand.rank}</strong></td>
                <td>
                    <div style="font-weight:600">${cand.candidate_name}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted)">${cand.filename}</div>
                </td>
                <td>
                    <div style="font-size:1.1rem; font-weight:700; color:var(--brand-accent)">${cand.overall_match_score}%</div>
                </td>
                <td><span class="badge badge-${cand.verdict_badge}">${cand.verdict}</span></td>
                <td>${cand.skill_score}%</td>
                <td>${cand.semantic_score}%</td>
                <td>${cand.experience_years} yrs</td>
                <td>
                    <button class="btn btn-secondary btn-sm view-cand-btn" data-rank="${cand.rank}">Quick View</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Add Quick View click listeners
        document.querySelectorAll('.view-cand-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const rank = parseInt(e.target.getAttribute('data-rank'));
                const candidate = data.candidates.find(c => c.rank === rank);
                if (candidate) {
                    showCandidateModal(candidate);
                }
            });
        });
    }

    function showCandidateModal(candidate) {
        alert(
            `Candidate: ${candidate.candidate_name}\n` +
            `Rank: #${candidate.rank} (${candidate.verdict} - ${candidate.overall_match_score}%)\n` +
            `Email: ${candidate.email || 'Not detected'}\n` +
            `Experience: ${candidate.experience_years} years\n` +
            `Matched Skills (${candidate.matched_skills_count}): ${candidate.matched_skills.join(', ')}\n` +
            `Missing Skills (${candidate.missing_skills_count}): ${candidate.missing_skills.join(', ')}`
        );
    }

    // CSV Export
    if (btnExportCsv) {
        btnExportCsv.addEventListener('click', () => {
            if (!lastBatchResults || !lastBatchResults.candidates) {
                showToast("No batch results available to export.", true);
                return;
            }

            const rows = [
                ["Rank", "Candidate Name", "Filename", "Email", "Overall Match Score (%)", "Verdict", "Skill Score (%)", "Semantic Score (%)", "Experience (Years)", "Matched Skills", "Missing Skills"]
            ];

            lastBatchResults.candidates.forEach(c => {
                rows.push([
                    c.rank,
                    `"${c.candidate_name}"`,
                    `"${c.filename}"`,
                    `"${c.email || ''}"`,
                    c.overall_match_score,
                    c.verdict,
                    c.skill_score,
                    c.semantic_score,
                    c.experience_years,
                    `"${c.matched_skills.join('; ')}"`,
                    `"${c.missing_skills.join('; ')}"`
                ]);
            });

            const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `Screening_Report_${new Date().toISOString().slice(0, 10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast("Screening report downloaded as CSV!");
        });
    }

    // ----------------------------------------------------
    // Tab 4: Skill Taxonomy Directory
    // ----------------------------------------------------
    let taxonomyLoaded = false;
    async function loadTaxonomy() {
        if (taxonomyLoaded) return;
        const container = document.getElementById('taxonomy-categories');
        try {
            const res = await fetch('/api/skills/taxonomy');
            const data = await res.json();
            document.getElementById('taxonomy-total-count').textContent = data.total_skills_tracked;

            container.innerHTML = '';
            for (const [category, skills] of Object.entries(data.categories)) {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.marginBottom = '1rem';

                let skillTagsHtml = '';
                for (const [canonical, aliases] of Object.entries(skills)) {
                    skillTagsHtml += `<span class="skill-tag additional" title="Recognized aliases: ${aliases.join(', ')}"><strong>${canonical}</strong></span>`;
                }

                card.innerHTML = `
                    <div class="card-title" style="font-size:0.95rem; margin-bottom:0.5rem">📁 ${category} (${Object.keys(skills).length} skills)</div>
                    <div class="skill-tags">${skillTagsHtml}</div>
                `;
                container.appendChild(card);
            }
            taxonomyLoaded = true;
        } catch (e) {
            console.error("Failed to load taxonomy", e);
        }
    }
});
