(function () {
  const container = document.querySelector('.card.resources');
  if (!container) {
    return;
  }

  const statusEl = document.getElementById('llm-status-pill');
  syncLLMKey(container, statusEl);

  const storageKey = container.dataset.storageKey || 'afe-resources';
  const saveButton = container.querySelector('[data-action="toggle-save"]');
  const openAllButton = container.querySelector('[data-action="open-all"]');
  const groupElements = container.querySelectorAll('.resource-group');

  const saved = loadState();
  const collapseState = saved.collapse || {};
  let librarySaved = !!saved.saved;

  groupElements.forEach((group, index) => {
    const topic = group.dataset.topic;
    const body = group.querySelector('.resource-group__body');
    const toggle = group.querySelector('.resource-group__toggle');
    const shouldOpen = collapseState.hasOwnProperty(topic) ? collapseState[topic] : index === 0;
    if (shouldOpen) {
      body.removeAttribute('hidden');
    }
    collapseState[topic] = shouldOpen;

    toggle.addEventListener('click', () => {
      const hidden = body.hasAttribute('hidden');
      if (hidden) {
        body.removeAttribute('hidden');
      } else {
        body.setAttribute('hidden', 'hidden');
      }
      collapseState[topic] = body.hasAttribute('hidden') ? false : true;
      persist();
    });

    group.querySelectorAll('[data-query]').forEach((button) => {
      button.addEventListener('click', () => {
        const query = button.dataset.query || '';
        openQuery(query);
      });
    });
  });

  updateSaveButton();

  if (saveButton) {
    saveButton.addEventListener('click', () => {
      librarySaved = !librarySaved;
      updateSaveButton();
      persist();
    });
  }

  if (openAllButton) {
    openAllButton.addEventListener('click', () => {
      const links = container.querySelectorAll('.resource-item[data-link]');
      links.forEach((item) => {
        const link = item.dataset.link;
        if (link && /^https?:/i.test(link)) {
          window.open(link, '_blank', 'noopener');
        }
      });
    });
  }

  function updateSaveButton() {
    if (!saveButton) {
      return;
    }
    saveButton.textContent = librarySaved ? 'Saved to Library' : 'Save to Library';
    saveButton.classList.toggle('button--active', librarySaved);
  }

  function openQuery(raw) {
    const query = (raw || '').replace(/^query:/i, '');
    const url = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
    window.open(url, '_blank', 'noopener');
  }

  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(storageKey) || '{}');
    } catch (error) {
      return {};
    }
  }

  function persist() {
    const payload = {
      collapse: collapseState,
      saved: librarySaved,
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(payload));
    } catch (error) {
      console.warn('Unable to persist resource preferences', error);
    }
  }

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
