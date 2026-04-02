document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('rankTableBody');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');

    const STORAGE_KEY = 'coupang_tracker_data';

    // 1. 초기 데이터 로드 (localStorage)
    let savedData = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];

    // 행 생성 함수
    function createRow(rowData = null) {
        const i = tableBody.children.length;
        rowData = rowData || { keyword: '', url: '', thumbnail: '', rank: '-', rankInclAd: '-', tags: [], history: [] };
        const tr = document.createElement('tr');
        tr.dataset.history = JSON.stringify(rowData.history || []);
        tr.innerHTML = `
            <td style="white-space: nowrap;">
                <i class="fas fa-grip-vertical drag-handle" style="color:#bbb; margin-right:5px; font-size:1.1em;" title="드래그하여 행 옮기기"></i>
                <span class="row-index">${i + 1}</span>
            </td>
            <td>
                <div class="thumb-wrapper" title="클릭하여 쿠팡 상품 페이지 열기" style="cursor: pointer; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    ${rowData.thumbnail ? `<img src="${rowData.thumbnail}" class="product-thumb">` : `<div class="thumb-placeholder"><i class="fas fa-image"></i></div>`}
                </div>
            </td>
            <td><input type="text" class="row-input keyword" value="${rowData.keyword}" placeholder="키워드 입력"></td>
            <td class="url-cell" title="수정하려면 버튼을 클릭하세요">
                <input type="text" class="row-input url" value="${rowData.url}" placeholder="URL 입력" style="display: ${rowData.url ? 'none' : 'block'};">
                <button class="url-edit-btn" style="display: ${rowData.url ? 'block' : 'none'};"><i class="fas fa-link"></i> 설정됨</button>
            </td>
            <td><span class="rank-value ${rowData.rank === '-' ? 'empty' : ''}">${rowData.rank}</span></td>
            <td><span class="rank-value-ad ${rowData.rankInclAd === '-' ? 'empty' : ''}">${rowData.rankInclAd}</span></td>
            <td>
                <div class="badge-group">
                    ${renderBadges(rowData.tags)}
                </div>
            </td>
            <td>
                <div style="display: flex; gap: 5px; justify-content: center;">
                    <button class="btn btn-primary btn-sm check-row-btn" data-index="${i}" title="순위 확인">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-secondary btn-sm chart-row-btn" data-index="${i}" title="추세 그래프">
                        <i class="fas fa-chart-line"></i>
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(tr);
    }

    // 2. 테이블 행 초기 생성
    const initialRowCount = Math.max(10, savedData.length);
    for (let i = 0; i < initialRowCount; i++) {
        createRow(savedData[i]);
    }

    // 새로운 키워드 추가 버튼
    const addRowBtn = document.getElementById('addRowBtn');
    if (addRowBtn) {
        addRowBtn.addEventListener('click', () => {
            createRow();
            // 행을 추가한 후 제일 밑으로 스크롤 이동
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        });
    }

    // 3. 개별 행 버튼 이벤트 통합 처리
    tableBody.addEventListener('click', async (e) => {
        // 순위 확인 버튼
        if (e.target.closest('.check-row-btn')) {
            const row = e.target.closest('tr');
            const index = Array.from(tableBody.children).indexOf(row);
            await executeRow(index);
        }

        // 썸네일 클릭 시 URL 이동
        if (e.target.closest('.thumb-wrapper')) {
            const row = e.target.closest('tr');
            let url = row.querySelector('.url').value.trim();
            if (url) {
                if (!url.startsWith('http')) url = 'https://www.coupang.com' + (url.startsWith('/') ? '' : '/') + url; // 호환성
                window.open(url, '_blank');
            } else {
                alert('연결된 로켓 상품 URL이 아직 없습니다. URL을 먼저 입력해 주세요.');
            }
        }

        // URL 숨김 버튼 (클릭 시 인풋창 노출)
        if (e.target.closest('.url-edit-btn')) {
            const btn = e.target.closest('.url-edit-btn');
            const td = btn.closest('td');
            const input = td.querySelector('.url');
            btn.style.display = 'none';
            input.style.display = 'block';
            input.focus();
        }

        // 차트 버튼 노출
        if (e.target.closest('.chart-row-btn')) {
            const row = e.target.closest('tr');
            const keyword = row.querySelector('.keyword').value || '키워드 미입력';

            let history = [];
            try { history = JSON.parse(row.dataset.history || '[]'); } catch (e) { }

            showChartModal(keyword, history);
        }
    });

    // 정렬 이벤트 (일반 순위 기준 오름/내림차순)
    let sortAsc = true;
    const sortRankBtn = document.getElementById('sortRankBtn');
    if (sortRankBtn) {
        sortRankBtn.addEventListener('click', () => {
            const rows = Array.from(tableBody.children);

            rows.sort((a, b) => {
                const rankA = a.querySelector('.rank-value').textContent.replace('위', '').trim();
                const rankB = b.querySelector('.rank-value').textContent.replace('위', '').trim();

                const valA = (rankA === '-' || rankA === '') ? Infinity : parseInt(rankA) || Infinity;
                const valB = (rankB === '-' || rankB === '') ? Infinity : parseInt(rankB) || Infinity;

                if (valA === valB) return 0;
                return sortAsc ? valA - valB : valB - valA;
            });

            rows.forEach((row, i) => {
                tableBody.appendChild(row); // DOM의 자리를 이동
                // # 번호 컬럼 텍스트 맞춤
                row.querySelector('.row-index').textContent = i + 1;
            });

            // 헤더 아이콘 변경
            sortRankBtn.innerHTML = `일반 순위 <i class="fas fa-sort-${sortAsc ? 'down' : 'up'}" style="color:var(--primary);"></i>`;
            sortAsc = !sortAsc;

            saveCurrentState();
        });
    }

    // 정렬 이벤트 (키워드 기준 가나다순/역순)
    let sortKwAsc = true;
    const sortKeywordBtn = document.getElementById('sortKeywordBtn');
    if (sortKeywordBtn) {
        sortKeywordBtn.addEventListener('click', () => {
            const rows = Array.from(tableBody.children);

            rows.sort((a, b) => {
                const kwA = a.querySelector('.keyword').value.trim();
                const kwB = b.querySelector('.keyword').value.trim();

                // 빈 값은 뒤로 밀려나도록
                if (!kwA && kwB) return 1;
                if (kwA && !kwB) return -1;

                if (kwA === kwB) return 0;
                if (sortKwAsc) return kwA.localeCompare(kwB); // 가나다순
                else return kwB.localeCompare(kwA);          // 역순
            });

            rows.forEach((row, i) => {
                tableBody.appendChild(row);
                row.querySelector('.row-index').textContent = i + 1;
            });

            sortKeywordBtn.innerHTML = `키워드 <i class="fas fa-sort-${sortKwAsc ? 'alpha-down' : 'alpha-up'}" style="color:var(--primary);"></i>`;
            sortKwAsc = !sortKwAsc;

            saveCurrentState();
        });
    }

    // 4. 전체 실행 버튼 이벤트
    const runAllBtn = document.getElementById('runAllBtn');
    runAllBtn.addEventListener('click', async () => {
        if (runAllBtn.disabled) return;

        const confirmRun = confirm('입력된 모든 항목에 대해 조회를 시작하시겠습니까?\n(차단 방지를 위해 하나씩 순차적으로 진행됩니다.)');
        if (!confirmRun) return;

        runAllBtn.disabled = true;
        setLoading(true);

        const rows = tableBody.children;
        for (let i = 0; i < rows.length; i++) {
            const keyword = rows[i].querySelector('.keyword').value.trim();
            const targetUrl = rows[i].querySelector('.url').value.trim();

            if (keyword && targetUrl) {
                // 현재 작업 중인 행 강조
                rows[i].style.backgroundColor = '#f0f7ff';
                console.log(`[RunAll] Processing row ${i + 1}: ${keyword}`);

                await executeRow(i, true); // true는 개별 setLoading을 하지 않음

                rows[i].style.backgroundColor = '';
                // 페이지 간 짧은 휴식 (차단 방지 보조)
                await new Promise(r => setTimeout(r, 1000));
            }
        }

        setLoading(false);
        runAllBtn.disabled = false;
        alert('모든 항목의 순위 확인이 완료되었습니다.');
    });

    // 핵심 실행 로직 분리
    async function executeRow(index, isBatch = false) {
        const row = tableBody.children[index];
        const keyword = row.querySelector('.keyword').value.trim();
        const targetUrl = row.querySelector('.url').value.trim();

        if (!keyword || !targetUrl) {
            if (!isBatch) alert('키워드와 URL을 모두 입력해 주세요.');
            return;
        }

        if (!isBatch) setLoading(true);

        // 시각적 피드백
        const rankEl = row.querySelector('.rank-value');
        rankEl.textContent = '...';
        rankEl.classList.add('empty');

        try {
            const response = await fetch('/api/check-rank', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword, targetUrl })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                updateRow(index, result.data);
            } else {
                if (!isBatch) alert(result.detail || result.message || '순위를 찾을 수 없거나 에러가 발생했습니다.');
                updateRowStatus(index, 'FAILED');
            }
        } catch (err) {
            console.error(err);
            if (!isBatch) alert('서버 통신 오류가 발생했습니다.');
            updateRowStatus(index, 'FAILED');
        } finally {
            if (!isBatch) setLoading(false);
        }
    }

    // 4. 전체 저장 버튼 이벤트
    saveAllBtn.addEventListener('click', async () => {
        saveCurrentState();

        // 백그라운드 스크립트가 볼 수 있도록 서버에도 동기화
        const rows = tableBody.children;
        const targets = [];
        for (let i = 0; i < rows.length; i++) {
            const keyword = rows[i].querySelector('.keyword').value.trim();
            const url = rows[i].querySelector('.url').value.trim();
            if (keyword && url) {
                targets.push({ keyword, url });
            }
        }
        try {
            await fetch('/api/save-targets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ targets })
            });
        } catch (e) { console.error(e); }

        alert('모든 입력값이 저장되었습니다.');
    });

    // ==========================================
    // 텔레그램 로직 (Telegram Logic)
    // ==========================================
    const tgSettingsBtn = document.getElementById('tgSettingsBtn');
    const sendTgBtn = document.getElementById('sendTgBtn');
    const tgModal = document.getElementById('tgModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const saveTgBtn = document.getElementById('saveTgBtn');

    const tgTokenInput = document.getElementById('tgToken');
    const tgChatIdInput = document.getElementById('tgChatId');

    // 설정창 열기/닫기
    tgSettingsBtn.addEventListener('click', () => {
        tgTokenInput.value = localStorage.getItem('tg_token') || '';
        tgChatIdInput.value = localStorage.getItem('tg_chat_id') || '';
        tgModal.classList.remove('hidden');
    });

    closeModalBtn.addEventListener('click', () => tgModal.classList.add('hidden'));

    // 뒷배경 클릭 시 닫기
    tgModal.addEventListener('click', (e) => {
        if (e.target === tgModal) tgModal.classList.add('hidden');
    });

    // 텔레그램 설정 저장
    saveTgBtn.addEventListener('click', () => {
        const token = tgTokenInput.value.trim();
        const chatId = tgChatIdInput.value.trim();

        if (!token || !chatId) {
            alert('토큰과 Chat ID를 모두 입력해주세요.');
            return;
        }

        localStorage.setItem('tg_token', token);
        localStorage.setItem('tg_chat_id', chatId);
        alert('텔레그램 설정이 기기에 저장되었습니다.');
        tgModal.classList.add('hidden');
    });

    // 텔레그램 리포트 전송
    sendTgBtn.addEventListener('click', async () => {
        const token = localStorage.getItem('tg_token') || '';
        const chatId = localStorage.getItem('tg_chat_id') || '';

        // 토큰과 Chat ID가 로컬에 없어도 서버의 tg_config.json에 저장되어 있으므로 그대로 진행합니다.

        // 전송할 데이터 수집
        const rows = tableBody.children;
        let reportData = [];

        for (let i = 0; i < rows.length; i++) {
            const keyword = rows[i].querySelector('.keyword').value.trim();
            const rank = rows[i].querySelector('.rank-value').textContent;
            const rankAd = rows[i].querySelector('.rank-value-ad').textContent;

            if (keyword && (rank !== '-' || rankAd !== '-')) {
                const badges = extractTags(rows[i]).join(', ');
                reportData.push(`🔹 <b>[${keyword}]</b>\n- 일반 순위: ${rank !== '-' ? rank + '위' : '순위 밖'}\n- 광고 노출: ${rankAd !== '-' ? rankAd + '번째' : '미노출'}\n- 배지: ${badges || '없음'}`);
            }
        }

        if (reportData.length === 0) {
            alert('전송할 결과 데이터가 없습니다. 먼저 순위 확인을 진행해주세요.');
            return;
        }

        const now = new Date().toLocaleString('ko-KR');
        const message = `🚀 <b>[쿠팡 랭킹 나우v2 리포트]</b>\n⏱ 측정 일시: ${now}\n─────────────────\n\n` + reportData.join('\n\n');

        const confirmSend = confirm('조회된 결과 데이터를 텔레그램으로 전송하시겠습니까?');
        if (!confirmSend) return;

        setLoading(true);
        try {
            const response = await fetch('/api/send-telegram', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, chat_id: chatId, message })
            });
            const result = await response.json();

            if (response.ok && result.success) {
                alert('텔레그램 보고서 전송이 완료되었습니다! 핸드폰을 확인해주세요.');
            } else {
                alert(`전송 실패: ${result.detail || result.message}`);
            }
        } catch (err) {
            console.error(err);
            alert('서버 통신 중 오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    });

    // ==========================================

    function renderBadges(tags) {
        if (!tags || tags.length === 0) return '';
        return tags.map(tag => {
            if (tag === 'ROCKET') return '<span class="status-badge rocket">로켓</span>';
            if (tag === 'AD') return '<span class="status-badge ad">광고</span>';
            return '';
        }).join('');
    }

    function updateRow(index, data) {
        const row = tableBody.children[index];
        const thumbWrapper = row.querySelector('.thumb-wrapper');
        const rankEl = row.querySelector('.rank-value');
        const rankAdEl = row.querySelector('.rank-value-ad');
        const badgeGroup = row.querySelector('.badge-group');

        if (data.Thumbnail) {
            thumbWrapper.innerHTML = `<img src="${data.Thumbnail}" class="product-thumb">`;
            // img 태그에 dataset으로 url 임시 저장 (전체 저장 시 사용)
            thumbWrapper.dataset.url = data.Thumbnail;
        }

        rankEl.textContent = data.Organic_Rank !== '-' ? `${data.Organic_Rank}위` : '-';
        if (data.Organic_Rank !== '-') rankEl.classList.remove('empty');
        else rankEl.classList.add('empty');

        rankAdEl.textContent = data.Ad_Rank !== '-' ? `${data.Ad_Rank}위` : '-';
        if (data.Ad_Rank !== '-') rankAdEl.classList.remove('empty');
        else rankAdEl.classList.add('empty');

        let tags = [];
        if (data.Rocket_Status === 'YES') tags.push('ROCKET');
        if (data.Ad_Status === 'YES' || data.Ad_Rank !== '-') tags.push('AD'); // 광고로 잡힌 적 있으면 뱃지 달아줌
        badgeGroup.innerHTML = renderBadges(tags);

        // 히스토리 누적 로직 (날짜별 1건 유지)
        let history = [];
        try { history = JSON.parse(row.dataset.history || '[]'); } catch (e) { }

        const today = new Date().toLocaleDateString('ko-KR', { month: '2-digit', day: '2-digit' });
        const todayIdx = history.findIndex(h => h.date === today);
        let numericRank = data.Organic_Rank !== '-' ? parseInt(data.Organic_Rank) : null;
        if (isNaN(numericRank)) numericRank = null; // 순위 밖인 경우

        if (todayIdx >= 0) {
            history[todayIdx].rank = numericRank;
        } else {
            history.push({ date: today, rank: numericRank });
        }

        // 너무 많이 쌓이지 않게 최근 30개만 유지
        if (history.length > 30) history = history.slice(history.length - 30);

        row.dataset.history = JSON.stringify(history);

        saveCurrentState();
    }

    function updateRowStatus(index, status) {
        const row = tableBody.children[index];
        const rankEl = row.querySelector('.rank-value');
        if (status === 'FAILED') {
            rankEl.textContent = '실패';
            rankEl.classList.add('empty');
        }
    }

    function saveCurrentState() {
        const data = [];
        const rows = tableBody.children;
        for (let i = 0; i < rows.length; i++) {
            const thumbImg = rows[i].querySelector('.product-thumb');
            const thumbUrl = thumbImg ? thumbImg.src : (rows[i].querySelector('.thumb-wrapper').dataset.url || '');

            let historyArr = [];
            try { historyArr = JSON.parse(rows[i].dataset.history || '[]'); } catch (e) { }

            data.push({
                keyword: rows[i].querySelector('.keyword').value,
                url: rows[i].querySelector('.url').value,
                thumbnail: thumbUrl,
                rank: rows[i].querySelector('.rank-value').textContent,
                rankInclAd: rows[i].querySelector('.rank-value-ad') ? rows[i].querySelector('.rank-value-ad').textContent : '-',
                tags: extractTags(rows[i]),
                history: historyArr
            });

            // 저장할 때 만약 url이 차 있다면 숨김 아이콘 모드로 자동 전환 (UX 개선)
            const urlInput = rows[i].querySelector('.url');
            const urlBtn = rows[i].querySelector('.url-edit-btn');
            if (urlInput.value.trim() !== '') {
                urlInput.style.display = 'none';
                urlBtn.style.display = 'block';
            }
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    }

    function extractTags(row) {
        const tags = [];
        if (row.querySelector('.status-badge.rocket')) tags.push('ROCKET');
        if (row.querySelector('.status-badge.ad')) tags.push('AD');
        return tags;
    }

    function setLoading(isLoading) {
        if (isLoading) loadingOverlay.classList.remove('hidden');
        else loadingOverlay.classList.add('hidden');
    }

    // ==========================================
    // 차트 (Chart.js) 로직
    // ==========================================
    const chartModal = document.getElementById('chartModal');
    const closeChartModalBtn = document.getElementById('closeChartModalBtn');
    let chartInstance = null;

    closeChartModalBtn.addEventListener('click', () => chartModal.classList.add('hidden'));
    chartModal.addEventListener('click', (e) => {
        if (e.target === chartModal) chartModal.classList.add('hidden');
    });

    function showChartModal(keyword, history) {
        document.getElementById('chartModalTitle').innerHTML = `<i class="fas fa-chart-line"></i> [${keyword}] 순위 변동 추이`;
        chartModal.classList.remove('hidden');

        const ctx = document.getElementById('rankChart').getContext('2d');
        if (chartInstance) chartInstance.destroy(); // 기존 차트 초기화

        if (history.length === 0) {
            chartInstance = new Chart(ctx, { type: 'line', data: { labels: ['데이터 없음'], datasets: [] } });
            return;
        }

        const labels = history.map(h => h.date);
        const dataPoints = history.map(h => h.rank);

        // 차트 디자인 최적화 (유려한 애플 스타일)
        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '순수 순위',
                    data: dataPoints,
                    borderColor: '#1a73e8',
                    backgroundColor: 'rgba(26, 115, 232, 0.15)',
                    borderWidth: 3,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: '#1a73e8',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    fill: true,
                    tension: 0.4 // 부드러운 곡선
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        reverse: true, // 1위가 그래프 맨 위로 가도록
                        beginAtZero: false,
                        grid: { borderDash: [5, 5] },
                        title: { display: true, text: '순위 (등)', color: '#666' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 10,
                        callbacks: {
                            label: function (context) {
                                return context.raw ? ` ${context.raw}위` : ' 순위 밖';
                            }
                        }
                    }
                }
            }
        });
    }

    // ==========================================
    // 드래그 앤 드롭 정렬 (SortableJS)
    // ==========================================
    if (typeof Sortable !== 'undefined') {
        new Sortable(tableBody, {
            handle: '.drag-handle', // drag handle selector
            animation: 150,
            ghostClass: 'dragging', // class applied to the dragged item
            onEnd: function () {
                // Drop 후 화면상의 새로운 순서대로 번호(Index)를 재지정하고 저장합니다.
                Array.from(tableBody.children).forEach((row, i) => {
                    row.querySelector('.row-index').textContent = i + 1;
                });
                saveCurrentState();
            }
        });
    }

});
