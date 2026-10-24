"""Admin web page for model mapping and profile configuration."""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>cgw - Claude Gateway</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 20px 32px; display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 20px; font-weight: 600; }
.header .subtitle { font-size: 13px; color: #8892b0; margin-top: 4px; }
.header-right { display: flex; align-items: center; gap: 12px; }
.header .env-badge { background: rgba(255,255,255,0.15); padding: 8px 16px; border-radius: 8px; font-size: 14px; cursor: pointer; }
.header .env-badge:hover { background: rgba(255,255,255,0.25); }
.lang-toggle { background: rgba(255,255,255,0.15); border: none; color: #fff; padding: 8px 14px; border-radius: 8px; font-size: 13px; cursor: pointer; font-weight: 500; }
.lang-toggle:hover { background: rgba(255,255,255,0.25); }
.container { max-width: 1100px; margin: 0 auto; padding: 24px 16px; }
.status-bar { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
.status-pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 13px; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; }
.status-dot.error { background: #ef4444; }
.status-dot.warning { background: #f59e0b; }
.status-dot.gray { background: #94a3b8; }
.card { background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.card h2 { font-size: 16px; margin-bottom: 16px; color: #1a1a2e; display: flex; align-items: center; gap: 8px; }
.card h2 .badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
.badge-green { background: #dcfce7; color: #166534; }
.badge-yellow { background: #fef3c7; color: #92400e; }
.badge-gray { background: #f1f5f9; color: #64748b; }
.badge-blue { background: #dbeafe; color: #1e40af; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.form-group { display: flex; flex-direction: column; }
.form-group label { font-size: 12px; font-weight: 600; color: #555; margin-bottom: 6px; }
.form-group input, .form-group select { padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; outline: none; transition: border-color 0.2s; }
.form-group input:focus, .form-group select:focus { border-color: #6366f1; }
.form-actions { display: flex; gap: 12px; }
.btn { padding: 10px 20px; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; transition: opacity 0.2s; }
.btn:hover { opacity: 0.85; }
.btn-primary { background: #6366f1; color: #fff; }
.btn-secondary { background: #e2e8f0; color: #475569; }
.btn-danger { background: #ef4444; color: #fff; }
.btn-success { background: #22c55e; color: #fff; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
table { width: 100%; border-collapse: collapse; margin-top: 16px; }
th { text-align: left; padding: 12px 24px; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
td { padding: 14px 24px; font-size: 14px; border-bottom: 1px solid #f1f5f9; }
tr:hover td { background: #f8fafc; }
td code { background: #f1f5f9; padding: 3px 8px; border-radius: 4px; font-size: 13px; }
.actions { display: flex; gap: 8px; }
.profile-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }
.profile-item { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border: 2px solid #e2e8f0; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.profile-item:hover { border-color: #c7d2fe; background: #f8fafc; }
.profile-item.active { border-color: #6366f1; background: #eef2ff; }
.profile-item .info { flex: 1; }
.profile-item .name { font-weight: 600; font-size: 15px; }
.profile-item .detail { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.pending-banner { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; display: none; }
.pending-banner .btn-group { margin-top: 10px; display: flex; gap: 10px; }
.error-banner { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; display: none; }
.desktop-info { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; font-size: 13px; }
.desktop-info .label { color: #94a3b8; font-size: 11px; margin-bottom: 2px; }
.desktop-info .value { color: #334155; font-weight: 500; }
.modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; align-items: center; justify-content: center; }
.modal-overlay.show { display: flex; }
.modal { background: #fff; border-radius: 12px; padding: 32px; max-width: 480px; width: 90%; max-height: 80vh; overflow-y: auto; }
.modal h3 { font-size: 18px; margin-bottom: 16px; color: #1a1a2e; }
.modal .warning { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 10px 14px; border-radius: 6px; font-size: 13px; margin-bottom: 20px; }
.modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px; }
.toast { position: fixed; top: 20px; right: 20px; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 500; z-index: 1000; transform: translateX(120%); transition: transform 0.3s ease; }
.toast.show { transform: translateX(0); }
.toast.success { background: #dcfce7; color: #166534; }
.toast.error { background: #fef2f2; color: #b91c1c; }
.toast.warning { background: #fef3c7; color: #92400e; }
.empty-state { text-align: center; padding: 48px 24px; color: #94a3b8; font-size: 14px; }
.config-banner { background: #fff; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 13px; color: #666; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.config-banner code { background: #f1f5f9; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
@media (max-width: 768px) {
  .form-grid, .desktop-info { grid-template-columns: 1fr; }
  .header { padding: 16px; flex-direction: column; gap: 12px; }
  .container { padding: 16px 8px; }
  th, td { padding: 10px 12px; }
}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>cgw - Claude Gateway</h1>
    <div class="subtitle" data-i18n="subtitle">Multi-Profile Model Gateway</div>
  </div>
  <div class="header-right">
    <button class="lang-toggle" id="langToggle" onclick="toggleLang()">中文</button>
    <div class="env-badge" id="envBadge" onclick="showProfilesModal()">
      <span id="activeEnvName">-</span> &#9662;
    </div>
  </div>
</div>

<div class="container">
  <div class="status-bar">
    <div class="status-pill"><div class="status-dot" id="statusDot"></div><span id="statusText" data-i18n="checking">Checking...</span></div>
    <div class="status-pill"><span><span data-i18n="models_label">Models</span>: <strong id="modelCount">0</strong></span></div>
    <div class="status-pill"><span><span data-i18n="upstream_label">Upstream</span>: <strong id="upstreamUrl">-</strong></span></div>
  </div>

  <div class="config-banner"><span data-i18n="config_label">Config</span>: <code id="configPath">~/.claude-gateway/profiles.json</code></div>
  <div class="error-banner" id="errorBanner"><div id="errorText"></div></div>
  <div class="pending-banner" id="pendingBanner">
    <strong data-i18n="pending_title">Pending Changes</strong> <span data-i18n="pending_desc">- Config synced to Claude Desktop. Restart required to apply.</span>
    <div class="btn-group">
      <button class="btn btn-success btn-sm" onclick="showApplyModal()" data-i18n="btn_apply_restart">Apply &amp; Restart Desktop</button>
      <button class="btn btn-danger btn-sm" onclick="discardPending()" data-i18n="btn_discard">Discard Changes</button>
    </div>
  </div>

  <div class="card">
    <h2 id="formTitle" data-i18n="add_model">Add Model Mapping</h2>
    <div class="form-grid">
      <div class="form-group"><label data-i18n="label_model_id">Claude Model ID</label><input type="text" id="inputId" placeholder="e.g. claude-opus-4-6"></div>
      <div class="form-group"><label data-i18n="label_upstream_model">Upstream Model</label><input type="text" id="inputUpstream" placeholder="e.g. your-model-pro"></div>
      <div class="form-group"><label data-i18n="label_display_name">Display Name</label><input type="text" id="inputDisplayName" placeholder="e.g. Your Model Pro"></div>
    </div>
    <div class="form-actions">
      <button class="btn btn-primary" id="btnSubmit" onclick="submitForm()" data-i18n="btn_add_mapping">Add Mapping</button>
      <button class="btn btn-secondary" id="btnCancel" onclick="cancelEdit()" style="display:none" data-i18n="btn_cancel">Cancel</button>
    </div>
  </div>

  <div class="card">
    <h2><span data-i18n="model_mappings">Model Mappings</span> <span class="badge badge-blue" id="modelProfileBadge">-</span></h2>
    <table>
      <thead><tr><th data-i18n="th_model_id">Claude Model ID</th><th data-i18n="th_upstream">Upstream</th><th data-i18n="th_display_name">Display Name</th><th data-i18n="th_actions">Actions</th></tr></thead>
      <tbody id="modelTable"></tbody>
    </table>
    <div class="empty-state" id="emptyState" style="display:none" data-i18n="no_models">No model mappings. Add one above.</div>
  </div>

  <div class="card">
    <h2><span data-i18n="desktop_integration">Claude Desktop Integration</span> <span class="badge badge-gray" id="desktopBadge" data-i18n="checking">Checking...</span></h2>
    <div class="desktop-info">
      <div><div class="label" data-i18n="install_status">Install Status</div><div class="value" id="desktopInstalled">-</div></div>
      <div><div class="label" data-i18n="run_status">Run Status</div><div class="value" id="desktopRunning">-</div></div>
      <div><div class="label" data-i18n="config_status">Config Status</div><div class="value" id="desktopConfigStatus">-</div></div>
      <div><div class="label" data-i18n="configured_models">Configured Models</div><div class="value" id="desktopModelCount">-</div></div>
    </div>
    <div class="form-actions" id="desktopActions">
      <button class="btn btn-primary" onclick="syncToDesktop()" data-i18n="btn_sync">Sync to Desktop</button>
      <button class="btn btn-success" id="btnApply" onclick="showApplyModal()" style="display:none" data-i18n="btn_apply_restart_short">Apply &amp; Restart</button>
      <button class="btn btn-danger" onclick="discardPending()" data-i18n="btn_discard">Discard Changes</button>
    </div>
    <div id="desktopDisabledMsg" style="display:none;color:#94a3b8;font-size:13px;" data-i18n="desktop_not_detected">Claude Desktop not detected. Integration features unavailable.</div>
  </div>
</div>

<div class="modal-overlay" id="profilesModal">
  <div class="modal">
    <h3 data-i18n="profile_mgmt">Profile Management</h3>
    <div class="profile-list" id="profileList"></div>
    <div class="form-actions">
      <button class="btn btn-primary" onclick="showAddProfileModal()" data-i18n="btn_add_profile">+ Add Profile</button>
      <button class="btn btn-secondary" onclick="hideModal('profilesModal')" data-i18n="btn_close">Close</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="profileFormModal">
  <div class="modal">
    <h3 id="profileFormTitle" data-i18n="add_profile">Add Profile</h3>
    <div class="form-grid">
      <div class="form-group"><label data-i18n="label_profile_name">Profile Name</label><input type="text" id="pfName" placeholder="e.g. default"></div>
      <div class="form-group"><label data-i18n="label_upstream_url">Upstream URL</label><input type="text" id="pfUrl" placeholder="https://api.your-provider.com/anthropic"></div>
      <div class="form-group"><label>API Key</label><input type="password" id="pfKey" placeholder="sk-..."></div>
      <div class="form-group"><label data-i18n="label_auth_scheme">Auth Scheme</label><select id="pfAuth"><option value="api-key">api-key</option><option value="x-api-key">x-api-key</option><option value="Authorization">Authorization (Bearer)</option></select></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="hideModal('profileFormModal')" data-i18n="btn_cancel">Cancel</button>
      <button class="btn btn-primary" onclick="saveProfile()" data-i18n="btn_save">Save</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="applyModal">
  <div class="modal">
    <h3 data-i18n="restart_title">Restart Claude Desktop</h3>
    <div class="warning" data-i18n="restart_warning">Restarting will interrupt all active sessions and tasks. Make sure you have no unsaved work.</div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="hideModal('applyModal')" data-i18n="btn_cancel">Cancel</button>
      <button class="btn btn-danger" onclick="confirmApply()" data-i18n="btn_confirm_restart">Confirm Restart</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
var LANG = localStorage.getItem('cgw_lang') || 'en';

var I18N = {
  en: {
    subtitle: 'Multi-Profile Model Gateway',
    checking: 'Checking...',
    models_label: 'Models',
    upstream_label: 'Upstream',
    config_label: 'Config',
    pending_title: 'Pending Changes',
    pending_desc: '- Config synced to Claude Desktop. Restart required to apply.',
    btn_apply_restart: 'Apply & Restart Desktop',
    btn_apply_restart_short: 'Apply & Restart',
    btn_discard: 'Discard Changes',
    add_model: 'Add Model Mapping',
    edit_model: 'Edit Model: ',
    label_model_id: 'Claude Model ID',
    label_upstream_model: 'Upstream Model',
    label_display_name: 'Display Name',
    btn_add_mapping: 'Add Mapping',
    btn_save: 'Save',
    btn_cancel: 'Cancel',
    model_mappings: 'Model Mappings',
    th_model_id: 'Claude Model ID',
    th_upstream: 'Upstream',
    th_display_name: 'Display Name',
    th_actions: 'Actions',
    no_models: 'No model mappings. Add one above.',
    desktop_integration: 'Claude Desktop Integration',
    install_status: 'Install Status',
    run_status: 'Run Status',
    config_status: 'Config Status',
    configured_models: 'Configured Models',
    btn_sync: 'Sync to Desktop',
    desktop_not_detected: 'Claude Desktop not detected. Integration features unavailable.',
    profile_mgmt: 'Profile Management',
    btn_add_profile: '+ Add Profile',
    btn_close: 'Close',
    add_profile: 'Add Profile',
    label_profile_name: 'Profile Name',
    label_upstream_url: 'Upstream URL',
    label_auth_scheme: 'Auth Scheme',
    restart_title: 'Restart Claude Desktop',
    restart_warning: 'Restarting will interrupt all active sessions and tasks. Make sure you have no unsaved work.',
    btn_confirm_restart: 'Confirm Restart',
    btn_edit: 'Edit',
    btn_delete: 'Delete',
    btn_switch: 'Switch',
    active_badge: 'Active',
    no_profiles: 'No profiles configured',
    models_word: 'models',
    // dynamic messages
    msg_running: 'Running',
    msg_stopped: 'Stopped',
    msg_installed: 'Installed',
    msg_not_installed: 'Not Installed',
    msg_running2: 'Running',
    msg_not_running: 'Not Running',
    msg_pending_restart: 'Pending Restart',
    msg_connected: 'Connected',
    msg_pending: 'Pending',
    msg_configured: 'Configured',
    msg_not_configured: 'Not Configured',
    msg_fill_required: 'Please fill in all required fields',
    msg_profile_created: 'Profile created: ',
    msg_profile_deleted: 'Profile deleted',
    msg_switched: 'Switched to ',
    msg_restart_gateway: '. Please restart the gateway.',
    msg_network_error: 'Network error',
    msg_updated: 'Updated',
    msg_added: 'Added',
    msg_deleted: 'Deleted',
    msg_synced: 'Synced. Click the Apply button to restart.',
    msg_restarting: 'Restarting Claude Desktop...',
    msg_restarted: 'Restarted successfully',
    msg_restart_failed: 'Restart failed',
    msg_config_discarded: 'Configuration discarded',
    confirm_delete_model: 'Delete this model?',
    confirm_delete_profile: 'Delete this profile?',
    confirm_discard: 'Discard pending configuration changes?',
    msg_failed: 'Failed',
    msg_create_failed: 'Failed to create profile',
    msg_switch_failed: 'Failed to switch profile',
    msg_delete_failed: 'Failed to delete profile',
    msg_sync_failed: 'Sync failed'
  },
  zh: {
    subtitle: '多环境模型网关',
    checking: '检测中...',
    models_label: '模型数',
    upstream_label: '上游',
    config_label: '配置文件',
    pending_title: '待生效变更',
    pending_desc: '— 配置已同步到 Claude Desktop，需重启生效。',
    btn_apply_restart: '生效并重启 Desktop',
    btn_apply_restart_short: '生效并重启',
    btn_discard: '丢弃变更',
    add_model: '添加模型映射',
    edit_model: '编辑模型：',
    label_model_id: 'Claude 模型 ID',
    label_upstream_model: '上游模型',
    label_display_name: '显示名称',
    btn_add_mapping: '添加映射',
    btn_save: '保存',
    btn_cancel: '取消',
    model_mappings: '模型映射',
    th_model_id: 'Claude 模型 ID',
    th_upstream: '上游模型',
    th_display_name: '显示名称',
    th_actions: '操作',
    no_models: '暂无模型映射，请在上方添加。',
    desktop_integration: 'Claude Desktop 集成',
    install_status: '安装状态',
    run_status: '运行状态',
    config_status: '配置状态',
    configured_models: '已配置模型',
    btn_sync: '同步到 Desktop',
    desktop_not_detected: '未检测到 Claude Desktop，集成功能不可用。',
    profile_mgmt: '环境管理',
    btn_add_profile: '+ 添加环境',
    btn_close: '关闭',
    add_profile: '添加环境',
    label_profile_name: '环境名称',
    label_upstream_url: '上游 URL',
    label_auth_scheme: '认证方式',
    restart_title: '重启 Claude Desktop',
    restart_warning: '重启将中断所有进行中的会话和任务，请确保没有未保存的工作。',
    btn_confirm_restart: '确认重启',
    btn_edit: '编辑',
    btn_delete: '删除',
    btn_switch: '切换',
    active_badge: '当前',
    no_profiles: '暂无环境配置',
    models_word: '个模型',
    msg_running: '运行中',
    msg_stopped: '未运行',
    msg_installed: '已安装',
    msg_not_installed: '未安装',
    msg_running2: '运行中',
    msg_not_running: '未运行',
    msg_pending_restart: '待重启生效',
    msg_connected: '已连接',
    msg_pending: '待生效',
    msg_configured: '已配置',
    msg_not_configured: '未配置',
    msg_fill_required: '请填写所有必填字段',
    msg_profile_created: '环境已创建：',
    msg_profile_deleted: '环境已删除',
    msg_switched: '已切换到 ',
    msg_restart_gateway: '，请重启网关。',
    msg_network_error: '网络错误',
    msg_updated: '已更新',
    msg_added: '已添加',
    msg_deleted: '已删除',
    msg_synced: '已同步，请点击生效按钮。',
    msg_restarting: '正在重启 Claude Desktop...',
    msg_restarted: '重启成功',
    msg_restart_failed: '重启失败',
    msg_config_discarded: '配置已丢弃',
    confirm_delete_model: '确定删除此模型？',
    confirm_delete_profile: '确定删除此环境？',
    confirm_discard: '确定丢弃待生效的配置变更？',
    msg_failed: '操作失败',
    msg_create_failed: '创建环境失败',
    msg_switch_failed: '切换环境失败',
    msg_delete_failed: '删除环境失败',
    msg_sync_failed: '同步失败'
  }
};

function t(key) {
  return (I18N[LANG] && I18N[LANG][key]) || (I18N.en[key] || key);
}

function applyLang() {
  document.documentElement.lang = LANG === 'zh' ? 'zh-CN' : 'en';
  document.getElementById('langToggle').textContent = LANG === 'zh' ? 'English' : '中文';
  var els = document.querySelectorAll('[data-i18n]');
  for (var i = 0; i < els.length; i++) {
    els[i].textContent = t(els[i].getAttribute('data-i18n'));
  }
}

function toggleLang() {
  LANG = LANG === 'en' ? 'zh' : 'en';
  localStorage.setItem('cgw_lang', LANG);
  applyLang();
  load();
}

var editingId = null;

function showToast(msg, type) {
  var el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast ' + type + ' show';
  setTimeout(function() { el.className = 'toast ' + type; }, 3000);
}

function showModal(id) { document.getElementById(id).className = 'modal-overlay show'; }
function hideModal(id) { document.getElementById(id).className = 'modal-overlay'; }

function renderTable(models) {
  var tbody = document.getElementById('modelTable');
  var empty = document.getElementById('emptyState');
  tbody.innerHTML = '';
  if (!models || models.length === 0) { empty.style.display = 'block'; return; }
  empty.style.display = 'none';
  for (var i = 0; i < models.length; i++) {
    var m = models[i];
    var tr = document.createElement('tr');
    tr.innerHTML = '<td><code></code></td><td><code></code></td><td></td><td class="actions"></td>';
    tr.cells[0].querySelector('code').textContent = m.id;
    tr.cells[1].querySelector('code').textContent = m.upstream;
    tr.cells[2].textContent = m.display_name || m.id;
    var td = tr.cells[3];
    var eb = document.createElement('button');
    eb.className = 'btn btn-secondary btn-sm'; eb.textContent = t('btn_edit');
    eb.onclick = (function(id){return function(){startEdit(id);}})(m.id);
    td.appendChild(eb);
    var db = document.createElement('button');
    db.className = 'btn btn-danger btn-sm'; db.textContent = t('btn_delete');
    db.onclick = (function(id){return function(){deleteModel(id);}})(m.id);
    td.appendChild(db);
    tbody.appendChild(tr);
  }
}

function renderProfiles(data) {
  var list = document.getElementById('profileList');
  list.innerHTML = '';
  var names = Object.keys(data.profiles || {});
  if (names.length === 0) {
    list.innerHTML = '<div class="empty-state">' + t('no_profiles') + '</div>';
    return;
  }
  for (var i = 0; i < names.length; i++) {
    var name = names[i];
    var p = data.profiles[name];
    var isActive = name === data.active;
    var div = document.createElement('div');
    div.className = 'profile-item' + (isActive ? ' active' : '');
    div.innerHTML = '<div class="info"><div class="name"></div><div class="detail"></div></div>';
    div.querySelector('.name').textContent = name;
    div.querySelector('.detail').textContent = p.upstream_url + ' \\u00b7 ' + (p.models||[]).length + ' ' + t('models_word');
    if (isActive) {
      var badge = document.createElement('span');
      badge.className = 'badge badge-green'; badge.textContent = t('active_badge');
      div.appendChild(badge);
    } else {
      var sw = document.createElement('button');
      sw.className = 'btn btn-primary btn-sm'; sw.textContent = t('btn_switch');
      sw.onclick = (function(n){return function(e){e.stopPropagation();switchProfile(n);}})(name);
      div.appendChild(sw);
    }
    var del = document.createElement('button');
    del.className = 'btn btn-danger btn-sm'; del.textContent = t('btn_delete');
    del.style.marginLeft = '8px';
    del.onclick = (function(n){return function(e){e.stopPropagation();deleteProfile(n);}})(name);
    div.appendChild(del);
    list.appendChild(div);
  }
}

function updateStatus(data) {
  document.getElementById('statusDot').className = 'status-dot';
  document.getElementById('statusText').textContent = t('msg_running');
  document.getElementById('modelCount').textContent = data.model_count || 0;
  document.getElementById('configPath').textContent = data.config_path || '-';
  if (data.upstream_base_url) document.getElementById('upstreamUrl').textContent = data.upstream_base_url;
  if (data.active_profile) {
    document.getElementById('activeEnvName').textContent = data.active_profile;
    document.getElementById('modelProfileBadge').textContent = data.active_profile;
  }
}

function updateDesktopStatus(data) {
  var installed = data.installed, pending = data.pending, config = data.config;
  document.getElementById('desktopInstalled').textContent = installed ? t('msg_installed') : t('msg_not_installed');
  document.getElementById('desktopRunning').textContent = data.running ? t('msg_running2') : t('msg_not_running');
  if (!installed) {
    document.getElementById('desktopBadge').className = 'badge badge-gray';
    document.getElementById('desktopBadge').textContent = t('msg_not_installed');
    document.getElementById('desktopActions').style.display = 'none';
    document.getElementById('desktopDisabledMsg').style.display = 'block';
    return;
  }
  document.getElementById('desktopActions').style.display = 'flex';
  document.getElementById('desktopDisabledMsg').style.display = 'none';
  if (pending) {
    document.getElementById('desktopBadge').className = 'badge badge-yellow';
    document.getElementById('desktopBadge').textContent = t('msg_pending');
    document.getElementById('pendingBanner').style.display = 'block';
    document.getElementById('btnApply').style.display = 'inline-block';
    document.getElementById('desktopConfigStatus').textContent = t('msg_pending_restart');
  } else {
    document.getElementById('desktopBadge').className = 'badge badge-green';
    document.getElementById('desktopBadge').textContent = t('msg_connected');
    document.getElementById('pendingBanner').style.display = 'none';
    document.getElementById('btnApply').style.display = 'none';
    document.getElementById('desktopConfigStatus').textContent = config ? t('msg_configured') : t('msg_not_configured');
  }
  document.getElementById('desktopModelCount').textContent = (config && config.inferenceModels) ? config.inferenceModels.length : 0;
}

function load() {
  fetch('/admin/api/status').then(function(r){return r.json();}).then(updateStatus);
  fetch('/admin/api/models').then(function(r){return r.json();}).then(function(d) {
    renderTable(d.models || []);
    if (d.profile) document.getElementById('modelProfileBadge').textContent = d.profile;
  });
  fetch('/admin/api/profiles').then(function(r){return r.json();}).then(function(d) {
    if (d.active) document.getElementById('activeEnvName').textContent = d.active;
    renderProfiles(d);
  });
  fetch('/admin/api/desktop/status').then(function(r){return r.json();}).then(updateDesktopStatus).catch(function(){});
}

function showProfilesModal() { load(); showModal('profilesModal'); }

function showAddProfileModal() {
  document.getElementById('profileFormTitle').textContent = t('add_profile');
  document.getElementById('pfName').value = '';
  document.getElementById('pfName').disabled = false;
  document.getElementById('pfUrl').value = '';
  document.getElementById('pfKey').value = '';
  document.getElementById('pfAuth').value = 'api-key';
  showModal('profileFormModal');
}

function saveProfile() {
  var name = document.getElementById('pfName').value.trim();
  var url = document.getElementById('pfUrl').value.trim();
  var key = document.getElementById('pfKey').value.trim();
  var auth = document.getElementById('pfAuth').value;
  if (!name || !url || !key) { showToast(t('msg_fill_required'), 'error'); return; }
  fetch('/admin/api/profiles', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: name, upstream_url: url, api_key: key, auth_scheme: auth})
  }).then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) {
      showToast(t('msg_profile_created') + name, 'success');
      hideModal('profileFormModal');
      load();
    } else {
      showToast(res.data.detail || t('msg_create_failed'), 'error');
    }
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function switchProfile(name) {
  fetch('/admin/api/profiles/switch', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: name})
  }).then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) {
      showToast(t('msg_switched') + name + t('msg_restart_gateway'), 'warning');
      hideModal('profilesModal');
      load();
    } else {
      showToast(res.data.detail || t('msg_switch_failed'), 'error');
    }
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function deleteProfile(name) {
  if (!confirm(t('confirm_delete_profile'))) return;
  fetch('/admin/api/profiles/' + encodeURIComponent(name), {method: 'DELETE'})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(t('msg_profile_deleted'), 'success'); load(); }
    else showToast(res.data.detail || t('msg_delete_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function submitForm() {
  var id = document.getElementById('inputId').value.trim();
  var upstream = document.getElementById('inputUpstream').value.trim();
  var display = document.getElementById('inputDisplayName').value.trim();
  if (!id || !upstream) { showToast(t('msg_fill_required'), 'error'); return; }
  var method = editingId ? 'PUT' : 'POST';
  var url = editingId ? '/admin/api/models/' + encodeURIComponent(editingId) : '/admin/api/models';
  fetch(url, {
    method: method, headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id, upstream: upstream, display_name: display})
  }).then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(editingId ? t('msg_updated') : t('msg_added'), 'success'); cancelEdit(); load(); }
    else showToast(res.data.detail || t('msg_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function startEdit(id) {
  fetch('/admin/api/models').then(function(r){return r.json();}).then(function(d) {
    for (var i = 0; i < (d.models||[]).length; i++) {
      if (d.models[i].id === id) {
        var m = d.models[i];
        document.getElementById('inputId').value = m.id;
        document.getElementById('inputUpstream').value = m.upstream;
        document.getElementById('inputDisplayName').value = m.display_name;
        editingId = id;
        document.getElementById('formTitle').textContent = t('edit_model') + id;
        document.getElementById('btnSubmit').textContent = t('btn_save');
        document.getElementById('btnCancel').style.display = 'inline-block';
        document.getElementById('inputId').disabled = true;
        return;
      }
    }
  });
}

function cancelEdit() {
  editingId = null;
  document.getElementById('formTitle').textContent = t('add_model');
  document.getElementById('btnSubmit').textContent = t('btn_add_mapping');
  document.getElementById('btnCancel').style.display = 'none';
  document.getElementById('inputId').disabled = false;
  document.getElementById('inputId').value = '';
  document.getElementById('inputUpstream').value = '';
  document.getElementById('inputDisplayName').value = '';
}

function deleteModel(id) {
  if (!confirm(t('confirm_delete_model'))) return;
  fetch('/admin/api/models/' + encodeURIComponent(id), {method: 'DELETE'})
  .then(function(r){return r.json();}).then(function(){ showToast(t('msg_deleted'), 'success'); load(); });
}

function syncToDesktop() {
  fetch('/admin/api/desktop/sync', {method: 'POST'})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(t('msg_synced'), 'success'); load(); }
    else showToast(res.data.detail || t('msg_sync_failed'), 'error');
  });
}

function showApplyModal() { showModal('applyModal'); }
function confirmApply() {
  hideModal('applyModal');
  showToast(t('msg_restarting'), 'warning');
  fetch('/admin/api/desktop/apply', {method: 'POST'})
  .then(function(r){return r.json();}).then(function(d) {
    if (d.ok) { showToast(t('msg_restarted'), 'success'); setTimeout(load, 3000); }
    else showToast(d.error || t('msg_restart_failed'), 'error');
  });
}

function discardPending() {
  if (!confirm(t('confirm_discard'))) return;
  fetch('/admin/api/desktop/discard', {method: 'POST'})
  .then(function(){ showToast(t('msg_config_discarded'), 'success'); load(); });
}

applyLang();
load();
</script>
</body>
</html>"""
