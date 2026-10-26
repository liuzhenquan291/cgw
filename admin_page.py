"""Admin web page for model mapping and profile configuration."""

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>cgw - Claude Gateway</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; color: #1a1a2e; min-height: 100vh; }
.header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 16px 28px; display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 18px; font-weight: 600; }
.header .subtitle { font-size: 12px; color: #8892b0; margin-top: 2px; }
.header-right { display: flex; align-items: center; gap: 10px; }
.lang-toggle { background: rgba(255,255,255,0.15); border: none; color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }
.lang-toggle:hover { background: rgba(255,255,255,0.25); }
.container { max-width: 1000px; margin: 0 auto; padding: 20px 16px 40px; }
.status-bar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.pill { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 16px; font-size: 12px; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; }
.dot.red { background: #ef4444; }
.dot.yellow { background: #f59e0b; }
.section-title { font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin: 24px 0 12px; display: flex; justify-content: space-between; align-items: center; }
.card { background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.profile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.profile-card { border: 2px solid #e2e8f0; border-radius: 10px; padding: 16px; cursor: pointer; transition: all 0.2s; position: relative; }
.profile-card:hover { border-color: #a5b4fc; background: #f8faff; }
.profile-card.active { border-color: #6366f1; background: #eef2ff; }
.profile-card .pc-name { font-weight: 700; font-size: 16px; margin-bottom: 4px; }
.profile-card .pc-info { font-size: 11px; color: #94a3b8; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.profile-card .pc-badge { position: absolute; top: 10px; right: 10px; font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
.profile-card .pc-actions { display: flex; gap: 6px; margin-top: 10px; }
.badge-green { background: #dcfce7; color: #166534; }
.badge-blue { background: #dbeafe; color: #1e40af; }
.btn { padding: 7px 16px; border: none; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; transition: opacity 0.15s; }
.btn:hover { opacity: 0.85; }
.btn-primary { background: #6366f1; color: #fff; }
.btn-sm { padding: 5px 10px; font-size: 11px; }
.btn-danger { background: #ef4444; color: #fff; }
.btn-success { background: #22c55e; color: #fff; }
.btn-secondary { background: #e2e8f0; color: #475569; }
.btn-warning { background: #f59e0b; color: #fff; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px; margin-bottom: 16px; }
.info-item .lbl { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
.info-item .val { font-size: 13px; color: #334155; font-weight: 500; word-break: break-all; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 10px 16px; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
td { padding: 12px 16px; font-size: 13px; border-bottom: 1px solid #f1f5f9; }
tr:hover td { background: #f8fafc; }
td code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
.actions { display: flex; gap: 6px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
.form-group { display: flex; flex-direction: column; }
.form-group label { font-size: 11px; font-weight: 600; color: #555; margin-bottom: 5px; }
.form-group input, .form-group select { padding: 9px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; outline: none; transition: border-color 0.2s; }
.form-group input:focus, .form-group select:focus { border-color: #6366f1; }
.form-actions { display: flex; gap: 10px; }
.modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; align-items: center; justify-content: center; }
.modal-overlay.show { display: flex; }
.modal { background: #fff; border-radius: 12px; padding: 28px; max-width: 520px; width: 92%; max-height: 85vh; overflow-y: auto; }
.modal h3 { font-size: 16px; margin-bottom: 16px; color: #1a1a2e; }
.modal .warn { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; padding: 10px 14px; border-radius: 6px; font-size: 12px; margin-bottom: 16px; line-height: 1.5; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
.toast { position: fixed; top: 20px; right: 20px; padding: 12px 20px; border-radius: 8px; font-size: 13px; font-weight: 500; z-index: 200; transform: translateX(120%); transition: transform 0.3s; }
.toast.show { transform: translateX(0); }
.toast.success { background: #dcfce7; color: #166534; }
.toast.error { background: #fef2f2; color: #b91c1c; }
.toast.warning { background: #fef3c7; color: #92400e; }
.empty { text-align: center; padding: 32px; color: #94a3b8; font-size: 13px; }
.pending-banner { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; display: none; }
.pending-banner .btns { margin-top: 8px; display: flex; gap: 8px; }
.desktop-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.desktop-grid .info-item .val { font-size: 13px; }
@media (max-width: 700px) {
  .form-grid, .info-grid, .desktop-grid { grid-template-columns: 1fr; }
  .profile-grid { grid-template-columns: 1fr 1fr; }
  .header { padding: 12px 16px; flex-wrap: wrap; }
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
    <button class="lang-toggle" onclick="toggleLang()" id="langBtn">中文</button>
  </div>
</div>

<div class="container">
  <div class="status-bar">
    <div class="pill"><div class="dot" id="sDot"></div><span id="sText" data-i18n="checking">Checking...</span></div>
    <div class="pill"><span data-i18n="models_label">Models</span>: <strong id="mCount">0</strong></div>
    <div class="pill"><span data-i18n="upstream_label">Upstream</span>: <strong id="uUrl" style="font-size:11px">-</strong></div>
    <div class="pill"><code id="cPath" style="font-size:10px">~/.claude-gateway/profiles.json</code></div>
    <div class="pill"><button class="btn btn-warning btn-sm" onclick="restartGateway()" data-i18n="btn_restart_gateway">Restart Gateway</button></div>
  </div>

  <div class="pending-banner" id="pendingBanner">
    <strong data-i18n="pending_title">Pending Changes</strong> <span data-i18n="pending_desc">- Synced to Claude Desktop, restart to apply.</span>
    <div class="btns">
      <button class="btn btn-success btn-sm" onclick="showModal('applyModal')" data-i18n="btn_apply_restart">Apply &amp; Restart Desktop</button>
      <button class="btn btn-danger btn-sm" onclick="discardPending()" data-i18n="btn_discard">Discard</button>
    </div>
  </div>

  <!-- Profile Groups -->
  <div class="section-title">
    <span data-i18n="profile_groups">Profile Groups</span>
    <button class="btn btn-primary btn-sm" onclick="showAddProfile()" data-i18n="btn_add_profile">+ Add Profile</button>
  </div>
  <div class="profile-grid" id="profileGrid"></div>

  <!-- Current Profile Config -->
  <div id="profileConfigSection">
    <div class="section-title"><span id="configSectionTitle">Profile Config</span></div>
    <div class="card">
      <div class="info-grid" id="profileInfo">
        <div class="info-item"><div class="lbl" data-i18n="label_profile_name">Profile Name</div><div class="val" id="pcName">-</div></div>
        <div class="info-item"><div class="lbl" data-i18n="label_upstream_url">Upstream URL</div><div class="val" id="pcUrl">-</div></div>
        <div class="info-item"><div class="lbl">API Key</div><div class="val" id="pcKey">-</div></div>
        <div class="info-item"><div class="lbl" data-i18n="label_auth_scheme">Auth Scheme</div><div class="val" id="pcAuth">-</div></div>
      </div>
      <div class="form-actions">
        <button class="btn btn-secondary btn-sm" onclick="editCurrentProfile()" data-i18n="btn_edit_config">Edit Config</button>
      </div>
    </div>

    <!-- Model Mappings -->
    <div class="section-title">
      <span id="modelSectionTitle">Model Mappings</span>
      <button class="btn btn-primary btn-sm" onclick="showAddModel()" data-i18n="btn_add_model">+ Add Model</button>
    </div>
    <div class="card">
      <table>
        <thead><tr><th data-i18n="th_model_id">Claude Model ID</th><th data-i18n="th_upstream">Upstream</th><th data-i18n="th_display_name">Display Name</th><th data-i18n="th_actions">Actions</th></tr></thead>
        <tbody id="modelTable"></tbody>
      </table>
      <div class="empty" id="emptyModels" style="display:none" data-i18n="no_models">No model mappings. Add one above.</div>
    </div>
  </div>

  <!-- No Profile State -->
  <div id="noProfileSection" style="display:none">
    <div class="card" style="border: 2px dashed #c7d2fe; background: #eef2ff;">
      <div class="empty" style="padding:24px;">
        <div style="font-size:24px;margin-bottom:8px;">&#128640;</div>
        <div style="font-size:15px;font-weight:600;color:#3730a3;margin-bottom:4px;" data-i18n="no_profile_title">No Profile Yet</div>
        <div style="font-size:13px;color:#6366f1;margin-bottom:16px;" data-i18n="no_profile_desc">Create your first profile to get started. A profile groups an upstream URL, API key, and model mappings together.</div>
        <button class="btn btn-primary" onclick="showAddProfile()" data-i18n="btn_create_profile">Create Profile</button>
      </div>
    </div>
  </div>

  <!-- Desktop Integration -->
  <div class="section-title"><span data-i18n="desktop_integration">Claude Desktop Integration</span></div>
  <div class="card">
    <div class="desktop-grid">
      <div class="info-item"><div class="lbl" data-i18n="install_status">Install Status</div><div class="val" id="dInstalled">-</div></div>
      <div class="info-item"><div class="lbl" data-i18n="run_status">Run Status</div><div class="val" id="dRunning">-</div></div>
      <div class="info-item"><div class="lbl" data-i18n="config_status">Config Status</div><div class="val" id="dConfig">-</div></div>
      <div class="info-item"><div class="lbl" data-i18n="configured_models">Configured Models</div><div class="val" id="dModels">-</div></div>
    </div>
    <div class="form-actions" id="dActions">
      <button class="btn btn-primary" onclick="syncDesktop()" data-i18n="btn_sync">Sync to Desktop</button>
      <button class="btn btn-success" id="btnApply" onclick="showModal('applyModal')" style="display:none" data-i18n="btn_apply_restart">Apply &amp; Restart</button>
      <button class="btn btn-danger" onclick="discardPending()" data-i18n="btn_discard">Discard</button>
    </div>
    <div id="dDisabled" class="empty" style="display:none;padding:16px;" data-i18n="desktop_not_detected">Claude Desktop not detected.</div>
  </div>
</div>

<!-- Add/Edit Profile Modal -->
<div class="modal-overlay" id="profileModal">
  <div class="modal">
    <h3 id="profileModalTitle" data-i18n="add_profile">Add Profile</h3>
    <div class="form-grid">
      <div class="form-group"><label data-i18n="label_profile_name">Profile Name</label><input type="text" id="pfName" placeholder="e.g. mimo"></div>
      <div class="form-group"><label data-i18n="label_upstream_url">Upstream URL</label><input type="text" id="pfUrl" placeholder="https://api.your-provider.com/anthropic"></div>
      <div class="form-group"><label>API Key</label><input type="password" id="pfKey" placeholder="sk-..."></div>
      <div class="form-group"><label data-i18n="label_auth_scheme">Auth Scheme</label>
        <select id="pfAuth"><option value="api-key">api-key</option><option value="x-api-key">x-api-key</option><option value="Authorization">Authorization (Bearer)</option></select>
      </div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="hideModal('profileModal')" data-i18n="btn_cancel">Cancel</button>
      <button class="btn btn-primary" onclick="saveProfile()" data-i18n="btn_save">Save</button>
    </div>
  </div>
</div>

<!-- Add/Edit Model Modal -->
<div class="modal-overlay" id="modelModal">
  <div class="modal">
    <h3 id="modelModalTitle" data-i18n="add_model">Add Model Mapping</h3>
    <div class="form-grid">
      <div class="form-group"><label data-i18n="label_model_id">Claude Model ID</label><input type="text" id="mdId" placeholder="e.g. claude-opus-4-6"></div>
      <div class="form-group"><label data-i18n="label_upstream_model">Upstream Model</label><input type="text" id="mdUpstream" placeholder="e.g. your-model-pro"></div>
      <div class="form-group"><label data-i18n="label_display_name">Display Name</label><input type="text" id="mdDisplay" placeholder="e.g. Your Model Pro"></div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="hideModal('modelModal')" data-i18n="btn_cancel">Cancel</button>
      <button class="btn btn-primary" onclick="saveModel()" data-i18n="btn_save">Save</button>
    </div>
  </div>
</div>

<!-- Apply Modal -->
<div class="modal-overlay" id="applyModal">
  <div class="modal">
    <h3 data-i18n="restart_title">Restart Claude Desktop</h3>
    <div class="warn" data-i18n="restart_warning">Restarting will interrupt all active sessions and tasks. Save your work first.</div>
    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="hideModal('applyModal')" data-i18n="btn_cancel">Cancel</button>
      <button class="btn btn-danger" onclick="confirmApply()" data-i18n="btn_confirm_restart">Confirm Restart</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
var LANG = localStorage.getItem('cgw_lang') || 'en';
var editModelId = null;
var editProfileName = null;

var I18N = {
  en: {
    subtitle: 'Multi-Profile Model Gateway', checking: 'Checking...',
    models_label: 'Models', upstream_label: 'Upstream',
    profile_groups: 'Profile Groups', btn_add_profile: '+ Add Profile',
    btn_create_profile: 'Create Profile', btn_edit_config: 'Edit Config',
    btn_add_model: '+ Add Model', btn_save: 'Save', btn_cancel: 'Cancel',
    btn_delete: 'Delete', btn_edit: 'Edit', btn_switch: 'Switch',
    btn_apply_restart: 'Apply & Restart Desktop', btn_discard: 'Discard',
    btn_sync: 'Sync to Desktop', btn_confirm_restart: 'Confirm Restart',
    btn_restart_gateway: 'Restart Gateway',
    btn_close: 'Close',
    add_profile: 'Add Profile', edit_profile: 'Edit Profile',
    add_model: 'Add Model Mapping', edit_model: 'Edit Model',
    label_profile_name: 'Profile Name', label_upstream_url: 'Upstream URL',
    label_auth_scheme: 'Auth Scheme', label_model_id: 'Claude Model ID',
    label_upstream_model: 'Upstream Model', label_display_name: 'Display Name',
    th_model_id: 'Claude Model ID', th_upstream: 'Upstream',
    th_display_name: 'Display Name', th_actions: 'Actions',
    no_models: 'No model mappings. Click "+ Add Model" to create one.',
    no_profile_title: 'No Profile Yet',
    no_profile_desc: 'Create your first profile to get started. A profile groups an upstream URL, API key, and model mappings together.',
    desktop_integration: 'Claude Desktop Integration',
    install_status: 'Install Status', run_status: 'Run Status',
    config_status: 'Config Status', configured_models: 'Configured Models',
    desktop_not_detected: 'Claude Desktop not detected.',
    restart_title: 'Restart Claude Desktop',
    restart_warning: 'Restarting will interrupt all active sessions and tasks. Save your work first.',
    pending_title: 'Pending Changes', pending_desc: '- Synced to Claude Desktop, restart to apply.',
    active_badge: 'ACTIVE', models_word: 'models',
    // dynamic
    msg_running: 'Running', msg_installed: 'Installed', msg_not_installed: 'Not Installed',
    msg_not_running: 'Not Running', msg_connected: 'Connected', msg_pending: 'Pending',
    msg_configured: 'Configured', msg_not_configured: 'Not Configured',
    msg_fill_required: 'Please fill in all required fields',
    msg_profile_created: 'Profile created: ', msg_profile_updated: 'Profile updated',
    msg_profile_deleted: 'Profile deleted', msg_switched: 'Switched to ',
    msg_model_added: 'Model added', msg_model_updated: 'Model updated',
    msg_model_deleted: 'Model deleted', msg_synced: 'Synced. Click Apply to restart.',
    msg_restarting: 'Restarting Claude Desktop...', msg_restarted: 'Restarted successfully',
    msg_restart_failed: 'Restart failed', msg_discarded: 'Changes discarded',
    msg_network_error: 'Network error', msg_failed: 'Failed',
    msg_config_error: 'Config Error',
    confirm_delete_model: 'Delete this model?', confirm_delete_profile: 'Delete this profile?',
    confirm_discard: 'Discard pending changes?', confirm_switch: 'Switch to this profile?'
  },
  zh: {
    subtitle: '多环境模型网关', checking: '检测中...',
    models_label: '模型数', upstream_label: '上游',
    profile_groups: '平台组', btn_add_profile: '+ 添加平台',
    btn_create_profile: '创建平台', btn_edit_config: '编辑配置',
    btn_add_model: '+ 添加模型', btn_save: '保存', btn_cancel: '取消',
    btn_delete: '删除', btn_edit: '编辑', btn_switch: '切换',
    btn_apply_restart: '生效并重启 Desktop', btn_discard: '丢弃',
    btn_sync: '同步到 Desktop', btn_confirm_restart: '确认重启',
    btn_restart_gateway: '重启网关',
    btn_close: '关闭',
    add_profile: '添加平台', edit_profile: '编辑平台',
    add_model: '添加模型映射', edit_model: '编辑模型',
    label_profile_name: '平台名称', label_upstream_url: '上游 URL',
    label_auth_scheme: '认证方式', label_model_id: 'Claude 模型 ID',
    label_upstream_model: '上游模型', label_display_name: '显示名称',
    th_model_id: 'Claude 模型 ID', th_upstream: '上游模型',
    th_display_name: '显示名称', th_actions: '操作',
    no_models: '暂无模型映射，点击「+ 添加模型」创建。',
    no_profile_title: '还没有平台配置',
    no_profile_desc: '创建您的第一个平台配置。一个平台包含上游 URL、API 密钥和模型映射。',
    desktop_integration: 'Claude Desktop 集成',
    install_status: '安装状态', run_status: '运行状态',
    config_status: '配置状态', configured_models: '已配置模型',
    desktop_not_detected: '未检测到 Claude Desktop。',
    restart_title: '重启 Claude Desktop',
    restart_warning: '重启将中断所有进行中的会话和任务，请先保存工作。',
    pending_title: '待生效变更', pending_desc: '— 已同步到 Claude Desktop，需重启生效。',
    active_badge: '当前', models_word: '个模型',
    msg_running: '运行中', msg_installed: '已安装', msg_not_installed: '未安装',
    msg_not_running: '未运行', msg_connected: '已连接', msg_pending: '待生效',
    msg_configured: '已配置', msg_not_configured: '未配置',
    msg_fill_required: '请填写所有必填字段',
    msg_profile_created: '平台已创建：', msg_profile_updated: '平台已更新',
    msg_profile_deleted: '平台已删除', msg_switched: '已切换到 ',
    msg_model_added: '模型已添加', msg_model_updated: '模型已更新',
    msg_model_deleted: '模型已删除', msg_synced: '已同步，请点击生效按钮。',
    msg_restarting: '正在重启 Claude Desktop...', msg_restarted: '重启成功',
    msg_restart_failed: '重启失败', msg_discarded: '变更已丢弃',
    msg_network_error: '网络错误', msg_failed: '操作失败',
    msg_config_error: '配置错误',
    confirm_delete_model: '确定删除此模型？', confirm_delete_profile: '确定删除此平台？',
    confirm_discard: '确定丢弃待生效的变更？', confirm_switch: '切换到此平台？'
  }
};

function t(k) { return (I18N[LANG] && I18N[LANG][k]) || I18N.en[k] || k; }

function applyLang() {
  document.documentElement.lang = LANG === 'zh' ? 'zh-CN' : 'en';
  document.getElementById('langBtn').textContent = LANG === 'zh' ? 'English' : '中文';
  var els = document.querySelectorAll('[data-i18n]');
  for (var i = 0; i < els.length; i++) els[i].textContent = t(els[i].getAttribute('data-i18n'));
}

function toggleLang() {
  LANG = LANG === 'en' ? 'zh' : 'en';
  localStorage.setItem('cgw_lang', LANG);
  applyLang();
  load();
}

function showToast(msg, type) {
  var el = document.getElementById('toast');
  el.textContent = msg; el.className = 'toast ' + type + ' show';
  setTimeout(function() { el.className = 'toast ' + type; }, 3000);
}

function showModal(id) { document.getElementById(id).className = 'modal-overlay show'; }
function hideModal(id) { document.getElementById(id).className = 'modal-overlay'; }

// ── Render Profile Groups ─────────────────────────

function renderProfiles(data) {
  var grid = document.getElementById('profileGrid');
  grid.innerHTML = '';
  var names = Object.keys(data.profiles || {});
  var active = data.active;

  for (var i = 0; i < names.length; i++) {
    var name = names[i];
    var p = data.profiles[name];
    var isActive = name === active;
    var div = document.createElement('div');
    div.className = 'profile-card' + (isActive ? ' active' : '');

    var badge = document.createElement('div');
    badge.className = 'pc-badge ' + (isActive ? 'badge-green' : 'badge-blue');
    badge.textContent = isActive ? t('active_badge') : (p.models||[]).length + ' ' + t('models_word');
    div.appendChild(badge);

    var nm = document.createElement('div');
    nm.className = 'pc-name'; nm.textContent = name;
    div.appendChild(nm);

    var info = document.createElement('div');
    info.className = 'pc-info'; info.textContent = p.upstream_url;
    div.appendChild(info);

    var actions = document.createElement('div');
    actions.className = 'pc-actions';

    if (!isActive) {
      var swBtn = document.createElement('button');
      swBtn.className = 'btn btn-primary btn-sm'; swBtn.textContent = t('btn_switch');
      swBtn.onclick = (function(n) { return function(e) { e.stopPropagation(); switchProfile(n); }; })(name);
      actions.appendChild(swBtn);
    }

    var editBtn = document.createElement('button');
    editBtn.className = 'btn btn-secondary btn-sm'; editBtn.textContent = t('btn_edit');
    editBtn.onclick = (function(n) { return function(e) { e.stopPropagation(); editProfile(n); }; })(name);
    actions.appendChild(editBtn);

    var delBtn = document.createElement('button');
    delBtn.className = 'btn btn-danger btn-sm'; delBtn.textContent = t('btn_delete');
    delBtn.onclick = (function(n) { return function(e) { e.stopPropagation(); deleteProfile(n); }; })(name);
    actions.appendChild(delBtn);

    div.appendChild(actions);
    grid.appendChild(div);
  }
}

// ── Render Current Profile Config ─────────────────

function renderProfileConfig(data) {
  var active = data.active;
  var p = data.profiles ? data.profiles[active] : null;
  var section = document.getElementById('profileConfigSection');
  var noProfile = document.getElementById('noProfileSection');

  if (!active || !p) {
    section.style.display = 'none';
    noProfile.style.display = 'block';
    return;
  }

  section.style.display = 'block';
  noProfile.style.display = 'none';

  document.getElementById('configSectionTitle').textContent = active + ' ' + t('profile_groups').replace('Groups', '').trim();
  document.getElementById('pcName').textContent = active;
  document.getElementById('pcUrl').textContent = p.upstream_url || '-';
  document.getElementById('pcKey').textContent = p.api_key || '-';
  document.getElementById('pcAuth').textContent = p.auth_scheme || 'api-key';
  document.getElementById('modelSectionTitle').textContent = active + ' ' + t('add_model').replace('Add', '').trim();
}

// ── Render Models ─────────────────────────────────

function renderModels(models) {
  var tbody = document.getElementById('modelTable');
  var empty = document.getElementById('emptyModels');
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
    eb.onclick = (function(id) { return function() { editModel(id); }; })(m.id);
    td.appendChild(eb);
    var db = document.createElement('button');
    db.className = 'btn btn-danger btn-sm'; db.textContent = t('btn_delete');
    db.onclick = (function(id) { return function() { deleteModel(id); }; })(m.id);
    td.appendChild(db);
    tbody.appendChild(tr);
  }
}

// ── Desktop Status ────────────────────────────────

function renderDesktop(data) {
  var installed = data.installed, pending = data.pending, config = data.config;
  document.getElementById('dInstalled').textContent = installed ? t('msg_installed') : t('msg_not_installed');
  document.getElementById('dRunning').textContent = data.running ? t('msg_running') : t('msg_not_running');

  if (!installed) {
    document.getElementById('dActions').style.display = 'none';
    document.getElementById('dDisabled').style.display = 'block';
    return;
  }
  document.getElementById('dActions').style.display = 'flex';
  document.getElementById('dDisabled').style.display = 'none';

  if (pending) {
    document.getElementById('dConfig').textContent = t('msg_pending');
    document.getElementById('pendingBanner').style.display = 'block';
    document.getElementById('btnApply').style.display = 'inline-block';
  } else {
    document.getElementById('dConfig').textContent = config ? t('msg_configured') : t('msg_not_configured');
    document.getElementById('pendingBanner').style.display = 'none';
    document.getElementById('btnApply').style.display = 'none';
  }
  document.getElementById('dModels').textContent = (config && config.inferenceModels) ? config.inferenceModels.length : 0;
}

// ── Load All Data ─────────────────────────────────

function load() {
  fetch('/admin/api/status').then(function(r){return r.json();}).then(function(d) {
    document.getElementById('sDot').className = d.ok ? 'dot' : 'dot red';
    document.getElementById('sText').textContent = d.ok ? t('msg_running') : t('msg_config_error');
    document.getElementById('mCount').textContent = d.model_count || 0;
    document.getElementById('uUrl').textContent = d.upstream_base_url || '-';
    document.getElementById('cPath').textContent = d.config_path || '-';
  }).catch(function(){});

  fetch('/admin/api/profiles').then(function(r){return r.json();}).then(function(d) {
    renderProfiles(d);
    renderProfileConfig(d);
  }).catch(function(){});

  fetch('/admin/api/models').then(function(r){return r.json();}).then(function(d) {
    renderModels(d.models || []);
  }).catch(function(){});

  fetch('/admin/api/desktop/status').then(function(r){return r.json();}).then(renderDesktop).catch(function(){});
}

// ── Profile CRUD ──────────────────────────────────

function showAddProfile() {
  editProfileName = null;
  document.getElementById('profileModalTitle').textContent = t('add_profile');
  document.getElementById('pfName').value = '';
  document.getElementById('pfName').disabled = false;
  document.getElementById('pfUrl').value = '';
  document.getElementById('pfKey').value = '';
  document.getElementById('pfAuth').value = 'api-key';
  showModal('profileModal');
}

function editProfile(name) {
  editProfileName = name;
  fetch('/admin/api/profiles').then(function(r){return r.json();}).then(function(d) {
    var p = d.profiles[name];
    if (!p) return;
    document.getElementById('profileModalTitle').textContent = t('edit_profile');
    document.getElementById('pfName').value = name;
    document.getElementById('pfName').disabled = true;
    document.getElementById('pfUrl').value = p.upstream_url || '';
    document.getElementById('pfKey').value = '';
    document.getElementById('pfKey').placeholder = '*** (leave blank to keep)';
    document.getElementById('pfAuth').value = p.auth_scheme || 'api-key';
    showModal('profileModal');
  });
}

function editCurrentProfile() {
  var name = document.getElementById('pcName').textContent;
  if (name && name !== '-') editProfile(name);
}

function saveProfile() {
  var name = document.getElementById('pfName').value.trim();
  var url = document.getElementById('pfUrl').value.trim();
  var key = document.getElementById('pfKey').value.trim();
  var auth = document.getElementById('pfAuth').value;

  if (!url) { showToast(t('msg_fill_required'), 'error'); return; }

  var method, api;
  if (editProfileName) {
    method = 'PUT';
    api = '/admin/api/profiles/' + encodeURIComponent(editProfileName);
    var body = {upstream_url: url, auth_scheme: auth};
    if (key) body.api_key = key;
    fetch(api, {
      method: method, headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    }).then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
    .then(function(res) {
      if (res.ok) { showToast(t('msg_profile_updated'), 'success'); hideModal('profileModal'); load(); }
      else showToast(res.data.detail || t('msg_failed'), 'error');
    }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
  } else {
    if (!name || !key) { showToast(t('msg_fill_required'), 'error'); return; }
    fetch('/admin/api/profiles', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name, upstream_url: url, api_key: key, auth_scheme: auth})
    }).then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
    .then(function(res) {
      if (res.ok) { showToast(t('msg_profile_created') + name, 'success'); hideModal('profileModal'); load(); }
      else showToast(res.data.detail || t('msg_failed'), 'error');
    }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
  }
}

function switchProfile(name) {
  if (!confirm(t('confirm_switch'))) return;
  fetch('/admin/api/profiles/switch', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: name})
  }).then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(t('msg_switched') + name, 'success'); load(); }
    else showToast(res.data.detail || t('msg_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function deleteProfile(name) {
  if (!confirm(t('confirm_delete_profile'))) return;
  fetch('/admin/api/profiles/' + encodeURIComponent(name), {method: 'DELETE'})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(t('msg_profile_deleted'), 'success'); load(); }
    else showToast(res.data.detail || t('msg_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

// ── Model CRUD ────────────────────────────────────

function showAddModel() {
  editModelId = null;
  document.getElementById('modelModalTitle').textContent = t('add_model');
  document.getElementById('mdId').value = '';
  document.getElementById('mdId').disabled = false;
  document.getElementById('mdUpstream').value = '';
  document.getElementById('mdDisplay').value = '';
  showModal('modelModal');
}

function editModel(id) {
  editModelId = id;
  fetch('/admin/api/models').then(function(r){return r.json();}).then(function(d) {
    for (var i = 0; i < (d.models||[]).length; i++) {
      if (d.models[i].id === id) {
        var m = d.models[i];
        document.getElementById('modelModalTitle').textContent = t('edit_model');
        document.getElementById('mdId').value = m.id;
        document.getElementById('mdId').disabled = true;
        document.getElementById('mdUpstream').value = m.upstream;
        document.getElementById('mdDisplay').value = m.display_name;
        showModal('modelModal');
        return;
      }
    }
  });
}

function saveModel() {
  var id = document.getElementById('mdId').value.trim();
  var upstream = document.getElementById('mdUpstream').value.trim();
  var display = document.getElementById('mdDisplay').value.trim();
  if (!id || !upstream) { showToast(t('msg_fill_required'), 'error'); return; }

  var method = editModelId ? 'PUT' : 'POST';
  var api = editModelId ? '/admin/api/models/' + encodeURIComponent(editModelId) : '/admin/api/models';
  fetch(api, {
    method: method, headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id, upstream: upstream, display_name: display})
  }).then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) {
      showToast(editModelId ? t('msg_model_updated') : t('msg_model_added'), 'success');
      hideModal('modelModal'); load();
    } else showToast(res.data.detail || t('msg_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function deleteModel(id) {
  if (!confirm(t('confirm_delete_model'))) return;
  fetch('/admin/api/models/' + encodeURIComponent(id), {method: 'DELETE'})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(t('msg_model_deleted'), 'success'); load(); }
    else showToast(res.data.detail || t('msg_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

// ── Desktop ───────────────────────────────────────

function syncDesktop() {
  fetch('/admin/api/desktop/sync', {method: 'POST'})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(t('msg_synced'), 'success'); load(); }
    else showToast(res.data.detail || t('msg_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function confirmApply() {
  hideModal('applyModal');
  showToast(t('msg_restarting'), 'warning');
  fetch('/admin/api/desktop/apply', {method: 'POST'})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok && res.data.ok) { showToast(t('msg_restarted'), 'success'); setTimeout(load, 3000); }
    else showToast((res.data && (res.data.detail || res.data.error)) || t('msg_restart_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function discardPending() {
  if (!confirm(t('confirm_discard'))) return;
  fetch('/admin/api/desktop/discard', {method: 'POST'})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,data:d};});})
  .then(function(res) {
    if (res.ok) { showToast(t('msg_discarded'), 'success'); load(); }
    else showToast(res.data.detail || t('msg_failed'), 'error');
  }).catch(function(){ showToast(t('msg_network_error'), 'error'); });
}

function restartGateway() {
  if (!confirm('Restart the gateway?')) return;
  showToast('Restarting gateway...', 'warning');
  fetch('/admin/api/gateway/restart', {method: 'POST'})
  .then(function(r){return r.json();})
  .then(function() {
    showToast('Gateway restarting. Refresh in 2 seconds.', 'success');
    setTimeout(function() { location.reload(); }, 2500);
  }).catch(function() {
    // Gateway may already be down during restart
    showToast('Gateway restarting. Refresh in 2 seconds.', 'success');
    setTimeout(function() { location.reload(); }, 2500);
  });
}

applyLang();
load();
</script>
</body>
</html>"""
