// source: ai; ai_generated: (C)
'use strict';
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="local-token"]').content;
let inspection = null;
let initial = true;
let lastState = null;
let pending = false;

function notice(message, error = false) {
  $('notice').textContent = message;
  $('notice').className = error ? 'error' : '';
}
async function api(path, body) {
  const options = {headers: {'X-Local-Token': token}};
  if (body !== undefined) {
    options.method = 'POST';
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }
  const result = await fetch(path, options);
  const data = await result.json();
  if (!result.ok) throw new Error(data.error || 'Lokal request fejlede.');
  return data;
}
function draw(state) {
  lastState = state;
  $('demo-banner').hidden = !state.demo;
  $('setup').hidden = state.demo;
  $('calibration').hidden = state.demo;
  $('connection').textContent = state.demo ? 'OFFLINE DEMO' : state.connected ? 'iPhone forbundet' : 'Ikke forbundet';
  $('calibration-status').textContent = state.config_ready ? 'Begge skærme kalibreret · ' + state.bundle_id : state.calibrated_feed ? 'Profilside gemt. Kalibrér nu Send Like-skærmen.' : 'Ingen kalibrering endnu.';
  $('attempts').textContent = state.run.attempts;
  $('observed').textContent = state.run.observed_next;
  $('run-status').textContent = ({idle: 'Klar', running: 'Kører', finished: 'Afsluttet', stopped: 'Stoppet'})[state.run.status] || state.run.status;
  $('reason').textContent = state.run.reason;
  if (initial) {
    for (const key of ['udid', 'team_id', 'wda_bundle_id', 'platform_version', 'connection_mode']) $(key).value = state.device[key] || (key === 'connection_mode' ? 'windows-preinstalled' : '');
    initial = false;
  }
  const busy = state.busy || pending;
  $('connect').disabled = busy || state.connected;
  $('disconnect').disabled = busy || !state.connected;
  $('inspect').disabled = busy || !state.connected;
  $('save-feed').disabled = busy || !inspection;
  $('save-send').disabled = busy || !inspection || !$('empty-confirmed').checked || !state.calibrated_feed;
  $('preview').disabled = busy || !state.connected || !state.config_ready;
  $('start').disabled = busy || !state.connected || !state.config_ready || !$('ack').checked;
  $('stop').disabled = !state.busy;
}
async function refresh() {
  try { draw(await api('/api/state')); }
  catch (error) { notice('Kontrolpanelets forbindelse er afbrudt. Kontrollér Terminal. ' + error.message, true); }
}
async function action(fn) {
  if (pending) return;
  pending = true;
  if (lastState) draw(lastState);
  try { await fn(); }
  catch (error) { notice(error.message, true); }
  finally { pending = false; await refresh(); }
}
$('connect').onclick = () => action(async () => {
  notice('Forbinder via Appium. Kontrollér WebDriverAgent og tunnelen i terminalen, hvis forbindelsen fejler.');
  const device = {};
  for (const key of ['udid', 'team_id', 'wda_bundle_id', 'platform_version', 'connection_mode']) device[key] = $(key).value;
  await api('/api/connect', {device});
  notice('Forbundet. Åbn nu Hinge manuelt på telefonen og kalibrér knapperne.');
});
$('disconnect').onclick = () => action(async () => {
  await api('/api/disconnect', {});
  inspection = null;
  notice('Forbindelsen er afbrudt.');
});
$('inspect').onclick = () => action(async () => {
  inspection = await api('/api/inspect', {});
  $('empty-confirmed').checked = false;
  $('inspection-info').textContent = inspection.bundle_id + ' · ' + inspection.buttons.length + ' synlige knapper · ' + inspection.input_count + ' inputfelter';
  for (const id of ['marker', 'like', 'send']) {
    const select = $(id);
    select.replaceChildren(new Option('Vælg knap…', ''));
    inspection.buttons.forEach((button, index) => {
      const text = `${index + 1}. ${button.name || button.label || '(uden navn)'}${button.value ? ' · value: ' + button.value : ''}`;
      select.add(new Option(text, String(index)));
    });
  }
  $('controls').textContent = inspection.buttons.map((b, i) => `${i + 1}. name=${JSON.stringify(b.name)}  label=${JSON.stringify(b.label)}  value=${JSON.stringify(b.value)}`).join('\n') || 'Ingen navngivne knapper fundet.';
  notice('Aflæst uden klik. Vælg de rigtige knapper nedenfor.');
});
function selected(id) {
  if ($(id).value === '') throw new Error('Vælg en knap i feltet: ' + id);
  return Number($(id).value);
}
$('save-feed').onclick = () => action(async () => {
  await api('/api/calibrate/feed', {inspection_id: inspection.inspection_id, marker: selected('marker'), like: selected('like')});
  inspection = null;
  notice('Profilside gemt. Tryk selv på hjertet på din iPhone, og aflæs derefter Send Like-skærmen.');
});
$('save-send').onclick = () => action(async () => {
  await api('/api/calibrate/send', {inspection_id: inspection.inspection_id, send: selected('send'), empty_confirmed: $('empty-confirmed').checked});
  inspection = null;
  notice('Kalibrering gemt. Luk send-dialogen manuelt, og gå tilbage til Discover før start.');
});
$('preview').onclick = () => action(async () => {
  const result = await api('/api/preview', {});
  notice(result.reason === 'preview' ? 'Kontrol OK — skærm: ' + result.next_action + '. Ingen knapper blev trykket.' : result.reason, result.status === 'stopped');
});
$('start').onclick = () => action(async () => {
  await api('/api/start', {acknowledged: $('ack').checked, max_likes: Number($('max-likes').value), max_seconds: Number($('max-seconds').value)});
  $('ack').checked = false;
  notice(lastState.demo ? 'Demo startet. Der sendes ingen rigtige likes.' : 'Session startet. Stop straks ved noget uventet.');
});
$('stop').onclick = async () => {
  try { const result = await api('/api/stop', {}); notice(result.note); }
  catch (error) { notice(error.message, true); }
  await refresh();
};
for (const id of ['ack', 'empty-confirmed']) $(id).onchange = () => lastState && draw(lastState);
refresh();
setInterval(refresh, 800);
