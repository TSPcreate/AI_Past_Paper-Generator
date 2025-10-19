(function () {
  const layout = document.querySelector('.notes-layout');
  const statusEl = document.getElementById('llm-status-pill');
  syncLLMKey(layout, statusEl);

  const revealButton = document.querySelector('[data-action="reveal-all"]');
  const printButton = document.querySelector('[data-action="print"]');
  const copyButton = document.querySelector('[data-action="copy"]');
  const copySelect = document.getElementById('copy-select');
  const answerButtons = document.querySelectorAll('[data-answer]');

  let revealAllActive = false;

  function toggleAnswer(id) {
    const target = document.getElementById(id);
    if (!target) {
      return;
    }
    const hidden = target.hasAttribute('hidden');
    if (hidden) {
      target.removeAttribute('hidden');
    } else {
      target.setAttribute('hidden', 'hidden');
    }
  }

  function setAllAnswers(visible) {
    document.querySelectorAll('.quick-checks__answer, .anchor-answer').forEach((element) => {
      if (visible) {
        element.removeAttribute('hidden');
      } else {
        element.setAttribute('hidden', 'hidden');
      }
    });
  }

  function onRevealAll() {
    revealAllActive = !revealAllActive;
    setAllAnswers(revealAllActive);
    if (revealButton) {
      revealButton.textContent = revealAllActive ? 'Hide all answers' : 'Reveal all answers';
    }
  }

  function onPrint() {
    window.print();
  }

  async function onCopy() {
    if (!copySelect) {
      return;
    }
    const targetId = copySelect.value;
    const card = document.getElementById(targetId);
    if (!card) {
      return;
    }
    const text = card.innerText || card.textContent || '';
    try {
      await navigator.clipboard.writeText(text.trim());
      if (copyButton) {
        const original = copyButton.textContent;
        copyButton.textContent = 'Copied!';
        setTimeout(() => {
          copyButton.textContent = original;
        }, 1500);
      }
    } catch (error) {
      console.warn('Unable to copy notes section', error);
    }
  }

  answerButtons.forEach((button) => {
    button.addEventListener('click', () => {
      if (revealAllActive) {
        return;
      }
      const targetId = button.dataset.answer;
      if (targetId) {
        toggleAnswer(targetId);
      }
    });
  });

  if (revealButton) {
    revealButton.addEventListener('click', onRevealAll);
  }
  if (printButton) {
    printButton.addEventListener('click', onPrint);
  }
  if (copyButton) {
    copyButton.addEventListener('click', onCopy);
  }

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
