(function () {
  const API_BASE = '';

  const $loading = $('#loading');
  const $errorAlert = $('#error-alert');

  $('#year').text(new Date().getFullYear());

  async function checkHealth() {
    const $status = $('#api-status');
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      const data = await res.json();
      if (data.aiConfigured) {
        $status.removeClass('badge-secondary badge-danger').addClass('badge-success ready').text('AI Ready');
      } else {
        $status.removeClass('badge-secondary badge-success').addClass('badge-danger not-ready')
          .text('API key not configured — add OPENAI_API_KEY to .env');
      }
    } catch {
      $status.removeClass('badge-secondary badge-success').addClass('badge-danger not-ready')
        .text('Server offline — run npm start');
    }
  }

  function showError(message) {
    $errorAlert.text(message).removeClass('d-none');
    setTimeout(() => $errorAlert.addClass('d-none'), 6000);
  }

  function formToObject(form) {
    const data = {};
    $(form).serializeArray().forEach(({ name, value }) => {
      if (value.trim()) data[name] = value.trim();
    });
    return data;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const $form = $(e.target);
    const tool = $form.data('tool');
    const payload = formToObject($form);

    $errorAlert.addClass('d-none');
    $loading.removeClass('d-none');
    $form.find('button[type="submit"]').prop('disabled', true);

    try {
      const res = await fetch(`${API_BASE}/api/generate/${tool}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Something went wrong.');
      }

      const $result = $(`#${tool}-result`);
      const $output = $(`#${tool}-output`);
      $output.text(data.result);
      $result.removeClass('d-none');

      if (tool === 'bio') {
        $('#bio-char-count').text(`${data.result.length} / 150 characters`);
      }
    } catch (err) {
      showError(err.message);
    } finally {
      $loading.addClass('d-none');
      $form.find('button[type="submit"]').prop('disabled', false);
    }
  }

  $('form[data-tool]').on('submit', handleSubmit);

  $('.copy-btn').on('click', function () {
    const targetId = $(this).data('target');
    const text = $(`#${targetId}`).text();

    navigator.clipboard.writeText(text).then(() => {
      const $btn = $(this);
      $btn.addClass('copied').html('<i class="fa fa-check"></i> Copied!');
      setTimeout(() => {
        $btn.removeClass('copied').html('<i class="fa fa-copy"></i> Copy');
      }, 2000);
    });
  });

  checkHealth();
})();
