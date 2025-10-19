(function () {
  const container = document.querySelector('.card.flashcards');
  const statusEl = document.getElementById('llm-status-pill');
  syncLLMKey(container, statusEl);

  const dataEl = document.getElementById('flashcard-data');
  if (!dataEl) {
    return;
  }

  const storageKey = dataEl.dataset.storageKey || 'afe-flashcards';
  const initialCards = JSON.parse(dataEl.textContent || '[]');

  const panel = document.getElementById('flashcard-panel');
  const frontEl = document.getElementById('card-front');
  const backEl = document.getElementById('card-back');
  const whyEl = document.getElementById('card-why');
  const hintEl = document.getElementById('card-hint');
  const topicEl = document.getElementById('card-topic');
  const difficultyEl = document.getElementById('card-difficulty');
  const skillEl = document.getElementById('card-skill');
  const dueEl = document.getElementById('card-due');
  const progressEl = document.getElementById('progress-pill');
  const streakEl = document.getElementById('streak-indicator');
  const filterForm = document.getElementById('flashcard-filters');
  const controls = document.querySelectorAll('.review-button');
  const actions = document.querySelectorAll('.flashcards__actions [data-action], .flashcard-panel__controls [data-action]');
  const helpToggle = document.querySelector('[data-action="toggle-help"]');
  const helpBody = document.querySelector('.keyboard-help__body');

  const savedState = loadState();
  const cards = mergeCards(initialCards, savedState.cards);
  let order = savedState.order.length ? savedState.order : cards.map((card) => card.id);
  order = normaliseOrder(order, cards);
  let index = Math.min(savedState.index, Math.max(order.length - 1, 0));
  let showBack = false;
  let filters = savedState.filters;
  const reviewedToday = new Set(savedState.reviewedToday);
  const hintDepth = savedState.hintDepth || {};

  function loadState() {
    try {
      const parsed = JSON.parse(localStorage.getItem(storageKey) || '{}');
      return {
        cards: parsed.cards || {},
        order: parsed.order || [],
        index: typeof parsed.index === 'number' ? parsed.index : 0,
        filters: parsed.filters || { topic: '', difficulty: '', skill_type: '' },
        reviewedToday: parsed.reviewedToday || [],
        hintDepth: parsed.hintDepth || {},
      };
    } catch (error) {
      return {
        cards: {},
        order: [],
        index: 0,
        filters: { topic: '', difficulty: '', skill_type: '' },
        reviewedToday: [],
        hintDepth: {},
      };
    }
  }

  function mergeCards(base, savedMap) {
    return base.map((card) => {
      const saved = savedMap[card.id] || {};
      return {
        ...card,
        ease: typeof saved.ease === 'number' ? saved.ease : card.ease || 2.3,
        interval_days:
          typeof saved.interval_days === 'number' ? saved.interval_days : card.interval_days || card.interval || 1,
        due_iso: saved.due_iso || card.due_iso,
        streak: typeof saved.streak === 'number' ? saved.streak : card.streak || 0,
      };
    });
  }

  function normaliseOrder(current, available) {
    const validIds = new Set(available.map((card) => card.id));
    const cleaned = current.filter((id) => validIds.has(id));
    available.forEach((card) => {
      if (!cleaned.includes(card.id)) {
        cleaned.push(card.id);
      }
    });
    return cleaned;
  }

  function persist() {
    const payload = {
      cards: cards.reduce((acc, card) => {
        acc[card.id] = {
          ease: card.ease,
          interval_days: card.interval_days,
          due_iso: card.due_iso,
          streak: card.streak,
        };
        return acc;
      }, {}),
      order,
      index,
      filters,
      reviewedToday: Array.from(reviewedToday),
      hintDepth,
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(payload));
    } catch (error) {
      console.warn('Unable to persist flashcard state', error);
    }
  }

  function workingIds() {
    return order.filter((id) => {
      const card = getCard(id);
      return (
        card &&
        (!filters.topic || card.topic === filters.topic) &&
        (!filters.difficulty || card.difficulty === filters.difficulty) &&
        (!filters.skill_type || card.skill_type === filters.skill_type)
      );
    });
  }

  function getCard(id) {
    return cards.find((card) => card.id === id);
  }

  function getCurrentCard() {
    const ids = workingIds();
    if (!ids.length) {
      return null;
    }
    if (index >= ids.length) {
      index = ids.length - 1;
    }
    return getCard(ids[Math.max(index, 0)]);
  }

  function clampEase(value) {
    return Math.max(1.3, Math.min(3.0, value));
  }

  function schedule(card, grade) {
    const now = new Date();
    const baseInterval = Math.max(card.interval_days || 1, 1);
    if (grade === 'again') {
      card.ease = clampEase(card.ease - 0.2);
      card.interval_days = 0;
      card.streak = 0;
    } else if (grade === 'hard') {
      card.ease = clampEase(card.ease - 0.15);
      card.interval_days = Math.max(1, Math.ceil(baseInterval * 1.2));
      card.streak = Math.max(card.streak, 0);
    } else if (grade === 'good') {
      card.ease = clampEase(card.ease + 0.1);
      card.interval_days = Math.max(1, Math.ceil(baseInterval * 2.5));
      card.streak = card.streak + 1;
    } else if (grade === 'easy') {
      card.ease = clampEase(card.ease + 0.15);
      card.interval_days = Math.max(1, Math.ceil(baseInterval * 3.5));
      card.streak = card.streak + 1;
    }
    const intervalDays = card.interval_days;
    const due = new Date(now.getTime() + intervalDays * 24 * 60 * 60 * 1000);
    card.due_iso = due.toISOString();
    if (grade === 'again') {
      card.due_iso = now.toISOString();
    }
    reviewedToday.add(card.id);
    hintDepth[card.id] = 0;
  }

  function render() {
    const ids = workingIds();
    if (!ids.length) {
      frontEl.textContent = 'No cards match the current filters.';
      backEl.hidden = true;
      whyEl.hidden = true;
      hintEl.hidden = true;
      topicEl.textContent = 'Topic';
      difficultyEl.textContent = 'Difficulty';
      skillEl.textContent = 'Skill focus';
      dueEl.textContent = '—';
      panel.dataset.side = 'front';
      progressEl.textContent = 'Today: 0/0';
      streakEl.innerHTML = '';
      return;
    }

    const card = getCard(ids[Math.max(Math.min(index, ids.length - 1), 0)]);
    topicEl.textContent = card.topic;
    difficultyEl.textContent = card.difficulty;
    skillEl.textContent = card.skill_type;
    dueEl.textContent = formatDue(card.due_iso);

    frontEl.textContent = card.front;
    backEl.innerHTML = formatMultiline(card.back);
    backEl.hidden = !showBack;

    if (card.why_wrong) {
      whyEl.innerHTML = `<strong>Why learners slip:</strong> ${formatMultiline(card.why_wrong)}`;
      whyEl.hidden = !showBack;
    } else {
      whyEl.hidden = true;
    }

    const hintCount = hintDepth[card.id] || 0;
    if (card.hints && card.hints.length && hintCount > 0) {
      hintEl.innerHTML = card.hints.slice(0, hintCount).map(formatMultiline).join('<br>');
      hintEl.hidden = false;
    } else {
      hintEl.hidden = true;
    }

    panel.dataset.side = showBack ? 'back' : 'front';
    streakEl.innerHTML = renderStreak(card.streak);
    progressEl.textContent = `Today: ${countReviewed(ids)}/${ids.length}`;
  }

  function formatDue(iso) {
    if (!iso) {
      return 'Due soon';
    }
    const due = new Date(iso);
    if (Number.isNaN(due.getTime())) {
      return 'Due soon';
    }
    const now = new Date();
    const diffDays = Math.round((due - now) / (24 * 60 * 60 * 1000));
    if (diffDays <= 0) {
      return 'Due now';
    }
    if (diffDays === 1) {
      return 'Due in 1 day';
    }
    return `Due in ${diffDays} days`;
  }

  function formatMultiline(text) {
    return (text || '')
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => `<span>${line}</span>`)
      .join('<br>');
  }

  function renderStreak(count) {
    const capped = Math.min(count, 5);
    const dots = [];
    for (let i = 0; i < 5; i += 1) {
      dots.push(`<span class="streak-dot ${i < capped ? 'streak-dot--active' : ''}"></span>`);
    }
    return `<span class="streak-label">Streak</span>${dots.join('')}`;
  }

  function countReviewed(ids) {
    return ids.reduce((acc, id) => (reviewedToday.has(id) ? acc + 1 : acc), 0);
  }

  function flipCard() {
    showBack = !showBack;
    render();
    persist();
  }

  function showHint() {
    const card = getCurrentCard();
    if (!card || !card.hints || !card.hints.length) {
      return;
    }
    const current = hintDepth[card.id] || 0;
    if (current >= card.hints.length) {
      return;
    }
    hintDepth[card.id] = current + 1;
    hintEl.hidden = false;
    render();
    persist();
  }

  function nextCard(step) {
    const ids = workingIds();
    if (!ids.length) {
      return;
    }
    index = (index + step + ids.length) % ids.length;
    showBack = false;
  }

  function resetAll() {
    localStorage.removeItem(storageKey);
    window.location.reload();
  }

  function shuffleOrder() {
    const ids = Array.from(order);
    for (let i = ids.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [ids[i], ids[j]] = [ids[j], ids[i]];
    }
    order = ids;
    index = 0;
    showBack = false;
    persist();
    render();
  }

  function exportCsv() {
    const ids = workingIds();
    if (!ids.length) {
      return;
    }
    const header = ['topic', 'difficulty', 'skill', 'front', 'back', 'hints', 'due', 'ease', 'interval_days', 'streak'];
    const rows = ids.map((id) => {
      const card = getCard(id);
      return [
        card.topic,
        card.difficulty,
        card.skill_type,
        sanitizeCsv(card.front),
        sanitizeCsv(card.back),
        sanitizeCsv((card.hints || []).join(' | ')),
        card.due_iso,
        card.ease.toFixed(2),
        card.interval_days,
        card.streak,
      ];
    });
    const csv = [header.join(','), ...rows.map((row) => row.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'afe-flashcards.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function sanitizeCsv(text) {
    const value = (text || '').replace(/"/g, '""');
    return `"${value}"`;
  }

  function onFilterChange(event) {
    const formData = new FormData(filterForm);
    filters = {
      topic: formData.get('topic') || '',
      difficulty: formData.get('difficulty') || '',
      skill_type: formData.get('skill_type') || '',
    };
    index = 0;
    showBack = false;
    render();
    persist();
  }

  function onGrade(event) {
    const grade = event.currentTarget.dataset.grade;
    if (!grade) {
      return;
    }
    const card = getCurrentCard();
    if (!card) {
      return;
    }
    schedule(card, grade);
    nextCard(1);
    render();
    persist();
  }

  function onAction(event) {
    const action = event.currentTarget.dataset.action;
    if (action === 'shuffle') {
      shuffleOrder();
    } else if (action === 'reset') {
      resetAll();
    } else if (action === 'export') {
      exportCsv();
    } else if (action === 'flip') {
      flipCard();
    } else if (action === 'hint') {
      showHint();
    }
  }

  function onKeyDown(event) {
    const tag = event.target.tagName.toLowerCase();
    if (['input', 'select', 'textarea', 'button'].includes(tag)) {
      return;
    }
    if (event.code === 'Space') {
      event.preventDefault();
      flipCard();
    } else if (event.key === 'ArrowRight') {
      nextCard(1);
      render();
      persist();
    } else if (event.key === 'ArrowLeft') {
      nextCard(-1);
      render();
      persist();
    } else if (event.key === '1') {
      scheduleAndAdvance('again');
    } else if (event.key === '2') {
      scheduleAndAdvance('hard');
    } else if (event.key === '3') {
      scheduleAndAdvance('good');
    } else if (event.key === '4') {
      scheduleAndAdvance('easy');
    } else if (event.key.toLowerCase() === 'h') {
      showHint();
    } else if (event.key.toLowerCase() === 'r') {
      resetAll();
    }
  }

  function scheduleAndAdvance(grade) {
    const card = getCurrentCard();
    if (!card) {
      return;
    }
    schedule(card, grade);
    nextCard(1);
    render();
    persist();
  }

  function toggleHelp() {
    if (!helpBody) {
      return;
    }
    const hidden = helpBody.hasAttribute('hidden');
    if (hidden) {
      helpBody.removeAttribute('hidden');
    } else {
      helpBody.setAttribute('hidden', 'hidden');
    }
  }

  if (filterForm) {
    filterForm.addEventListener('change', onFilterChange);
    const topicSelect = filterForm.elements.namedItem('topic');
    const difficultySelect = filterForm.elements.namedItem('difficulty');
    const skillSelect = filterForm.elements.namedItem('skill_type');
    if (topicSelect) {
      topicSelect.value = filters.topic;
    }
    if (difficultySelect) {
      difficultySelect.value = filters.difficulty;
    }
    if (skillSelect) {
      skillSelect.value = filters.skill_type;
    }
  }

  controls.forEach((button) => button.addEventListener('click', onGrade));
  actions.forEach((button) => button.addEventListener('click', onAction));
  document.addEventListener('keydown', onKeyDown);
  if (helpToggle) {
    helpToggle.addEventListener('click', toggleHelp);
  }

  render();
  persist();

  function syncLLMKey(element, statusElement) {
    if (!element) {
      return '';
    }
    let key = element.dataset.llmKey || '';
    try {
      const stored = localStorage.getItem('afe-llm-key');
      if (key) {
        localStorage.setItem('afe-llm-key', key);
      } else if (stored) {
        key = stored;
        element.dataset.llmKey = stored;
      }
    } catch (error) {
      console.warn('Unable to access localStorage for LLM key', error);
    }

    if (statusElement) {
      if (key) {
        statusElement.textContent = `LLM key synced (••••${key.slice(-4)})`;
        statusElement.classList.add('llm-status__pill--active');
        statusElement.classList.remove('llm-status__pill--missing');
      } else {
        statusElement.textContent = 'Add your LLM key on the generator page to enable AI enhancements.';
        statusElement.classList.remove('llm-status__pill--active');
        statusElement.classList.add('llm-status__pill--missing');
      }
    }

    return key;
  }
})();
