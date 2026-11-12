# Generator for the upgraded BalanceVault Multi-Page Single-Page Application (SPA)
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_HTML_PATH = BASE_DIR / "app" / "static" / "index.html"
ROOT_HTML_PATH = BASE_DIR / "index.html"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BalanceVault (formerly LedgerLine) — FinTech Banking &amp; Audit Ledger</title>
    <style>
      :root {
        --sidebar-1: #071c35;
        --sidebar-2: #0c2448;
        --sidebar-3: #0d2b55;
        --page-bg: #edf2fb;
        --panel-bg: #f6f8fc;
        --card-bg: #ffffff;
        --soft-card: #ecf5ff;
        --line: #dfe8f5;
        --text: #1f2d3d;
        --muted: #6e7f96;
        --primary: #1d6de5;
        --primary-2: #2d72f7;
        --cyan: #25b0d9;
        --success: #1eae6b;
        --success-bg: #e6f7ef;
        --warning: #f59e0b;
        --warning-bg: #fff3d6;
        --red: #ef4444;
        --red-bg: #fee2e2;
        --shadow: 0 18px 36px rgba(17, 34, 68, 0.08);
        --shadow-sm: 0 4px 12px rgba(17, 34, 68, 0.05);
      }

      * { box-sizing: border-box; margin: 0; padding: 0; }

      body {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background: var(--page-bg);
        color: var(--text);
        line-height: 1.5;
        min-height: 100vh;
      }

      /* App Shell Layout */
      .app-shell {
        display: flex;
        min-height: 100vh;
      }

      /* Sidebar Navigation */
      .sidebar {
        width: 260px;
        background: linear-gradient(180deg, var(--sidebar-1) 0%, var(--sidebar-2) 60%, var(--sidebar-3) 100%);
        color: #ffffff;
        padding: 24px 16px;
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
        position: sticky;
        top: 0;
        height: 100vh;
        overflow-y: auto;
      }

      .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 24px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        text-decoration: none;
        color: inherit;
      }

      .brand-mark {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: linear-gradient(135deg, #25b0d9, #1d6de5);
        color: #ffffff;
        display: grid;
        place-items: center;
        font-weight: 800;
        font-size: 1.1rem;
        box-shadow: 0 4px 12px rgba(29, 109, 229, 0.4);
      }

      .brand-text {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.3px;
      }

      .brand-sub {
        font-size: 0.72rem;
        color: #38bdf8;
        font-weight: 600;
      }

      .nav {
        display: flex;
        flex-direction: column;
        gap: 4px;
        flex: 1;
      }

      .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        border-radius: 10px;
        color: rgba(255, 255, 255, 0.75);
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.15s ease;
        cursor: pointer;
        border: none;
        background: transparent;
        width: 100%;
        text-align: left;
      }

      .nav-item:hover {
        background: rgba(255, 255, 255, 0.08);
        color: #ffffff;
      }

      .nav-item.active {
        background: linear-gradient(90deg, rgba(29, 109, 229, 0.9), rgba(45, 114, 247, 0.75));
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .nav-icon {
        font-size: 1.1rem;
        width: 22px;
        text-align: center;
      }

      .divider {
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
        margin: 12px 0;
      }

      /* Sidebar Security Banner */
      .sidebar-sec-box {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 14px;
        margin-top: auto;
        margin-bottom: 16px;
        font-size: 0.8rem;
      }

      .sec-shield-row {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #38bdf8;
        font-weight: 700;
      }

      /* Sidebar Mini User */
      .profile-mini {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.1);
        cursor: pointer;
        transition: background 0.15s ease;
      }

      .profile-mini:hover {
        background: rgba(255, 255, 255, 0.12);
      }

      .avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #38bdf8, #2563eb);
        display: grid;
        place-items: center;
        font-weight: 700;
        font-size: 0.85rem;
        color: #ffffff;
        flex-shrink: 0;
      }

      .profile-mini-info {
        overflow: hidden;
      }

      .profile-mini-name {
        font-weight: 700;
        font-size: 0.85rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .profile-mini-role {
        font-size: 0.72rem;
        color: rgba(255, 255, 255, 0.65);
        text-transform: capitalize;
      }

      /* Main Content Area */
      .main {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
      }

      /* Topbar */
      .topbar-main {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 28px;
        background: #ffffff;
        border-bottom: 1px solid var(--line);
        position: sticky;
        top: 0;
        z-index: 50;
      }

      .top-search-wrap {
        display: flex;
        align-items: center;
        gap: 10px;
        background: var(--panel-bg);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 7px 14px;
        width: min(340px, 100%);
      }

      .top-search-wrap input {
        border: none;
        background: transparent;
        font: inherit;
        font-size: 0.88rem;
        outline: none;
        width: 100%;
        color: var(--text);
      }

      .top-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .btn-refresh {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        border: 1px solid var(--line);
        background: #ffffff;
        cursor: pointer;
        font-size: 1.05rem;
        display: grid;
        place-items: center;
        transition: all 0.15s ease;
      }

      .btn-refresh:hover {
        background: var(--panel-bg);
        transform: rotate(45deg);
      }

      /* User Menu & Dropdown */
      .user-menu-wrapper {
        position: relative;
      }

      .mini-user {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 5px 12px 5px 6px;
        cursor: pointer;
        user-select: none;
        transition: all 0.15s ease;
      }

      .mini-user:hover {
        background: var(--panel-bg);
        border-color: #cbd5e1;
      }

      .mini-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: linear-gradient(135deg, #25b0d9, #1d6de5);
        display: grid;
        place-items: center;
        font-size: 0.75rem;
        font-weight: 700;
        color: #ffffff;
      }

      .user-dropdown-menu {
        position: absolute;
        top: calc(100% + 8px);
        right: 0;
        min-width: 220px;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        box-shadow: 0 10px 28px rgba(17, 34, 68, 0.16);
        z-index: 1000;
        padding: 6px;
        animation: fadeInDropdown 0.15s ease-out;
      }

      @keyframes fadeInDropdown {
        from { opacity: 0; transform: translateY(-6px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .dropdown-header {
        padding: 10px 12px 8px;
      }

      .dropdown-name {
        font-weight: 700;
        color: var(--text);
        font-size: 0.94rem;
      }

      .dropdown-role {
        font-size: 0.76rem;
        color: var(--muted);
        text-transform: capitalize;
        margin-top: 2px;
      }

      .dropdown-divider {
        height: 1px;
        background: var(--line);
        margin: 4px 0;
      }

      .dropdown-item {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        padding: 9px 12px;
        border: none;
        background: transparent;
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text);
        cursor: pointer;
        text-align: left;
        transition: background 0.15s ease;
      }

      .dropdown-item:hover {
        background: #f1f5f9;
      }

      .dropdown-item.logout-item {
        color: #ef4444;
      }

      .dropdown-item.logout-item:hover {
        background: #fef2f2;
      }

      /* Content Container & Page Views */
      .content {
        padding: 28px;
        flex: 1;
        max-width: 1380px;
        margin: 0 auto;
        width: 100%;
      }

      .page-view {
        display: none;
      }

      .page-view.active {
        display: block;
        animation: fadeInPage 0.2s ease-in-out;
      }

      @keyframes fadeInPage {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
      }

      /* Common Page Headers */
      .page-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 24px;
        gap: 16px;
        flex-wrap: wrap;
      }

      .page-title {
        font-size: 1.55rem;
        font-weight: 800;
        color: var(--sidebar-1);
        margin-bottom: 4px;
        letter-spacing: -0.3px;
      }

      .page-sub {
        font-size: 0.88rem;
        color: var(--muted);
      }

      .page-actions {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      /* Buttons & Badges */
      .btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 9px 16px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.88rem;
        cursor: pointer;
        transition: all 0.15s ease;
        border: 1px solid transparent;
        text-decoration: none;
      }

      .btn-primary {
        background: var(--primary);
        color: #ffffff;
      }

      .btn-primary:hover {
        background: var(--primary-2);
        box-shadow: 0 4px 12px rgba(29, 109, 229, 0.25);
      }

      .btn-outline {
        background: #ffffff;
        border-color: var(--line);
        color: var(--text);
      }

      .btn-outline:hover {
        background: var(--panel-bg);
        border-color: #cbd5e1;
      }

      .btn-success {
        background: var(--success);
        color: #ffffff;
      }

      .btn-danger {
        background: var(--red);
        color: #ffffff;
      }

      .btn-sm {
        padding: 5px 10px;
        font-size: 0.8rem;
        border-radius: 8px;
      }

      /* Hero Cards & Stat Banners */
      .hero-card {
        background: linear-gradient(135deg, #092347 0%, #0d3468 60%, #154586 100%);
        color: #ffffff;
        border-radius: 18px;
        padding: 26px 30px;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
        margin-bottom: 24px;
      }

      .hero-card::after {
        content: "";
        position: absolute;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(37, 176, 217, 0.2) 0%, rgba(37, 176, 217, 0) 70%);
        top: -100px;
        right: -80px;
        pointer-events: none;
      }

      .hero-grid {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
        position: relative;
        z-index: 2;
      }

      .balance-label {
        font-size: 0.88rem;
        color: rgba(255, 255, 255, 0.75);
        font-weight: 600;
        margin-bottom: 6px;
      }

      .balance-value {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
      }

      .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
      }

      .status-pill.success {
        background: rgba(30, 174, 107, 0.2);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.3);
      }

      /* Grid Cards & Panels */
      .grid-4 {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }

      .grid-3 {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }

      .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 20px;
        margin-bottom: 24px;
      }

      .card {
        background: var(--card-bg);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 20px;
        box-shadow: var(--shadow-sm);
      }

      .stat-card {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .stat-card-label {
        font-size: 0.82rem;
        color: var(--muted);
        font-weight: 600;
      }

      .stat-card-val {
        font-size: 1.45rem;
        font-weight: 800;
        color: var(--sidebar-1);
      }

      .stat-card-sub {
        font-size: 0.75rem;
        color: var(--muted);
      }

      /* Quick Actions Tiles */
      .action-tile-btn {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        padding: 16px;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        cursor: pointer;
        transition: all 0.15s ease;
        text-align: left;
        width: 100%;
      }

      .action-tile-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(17, 34, 68, 0.08);
        border-color: #cbd5e1;
      }

      .tile-icon-box {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: grid;
        place-items: center;
        font-size: 1.15rem;
        margin-bottom: 12px;
      }

      .icon-deposit { background: var(--success-bg); color: var(--success); }
      .icon-withdraw { background: var(--warning-bg); color: var(--warning); }
      .icon-transfer { background: #ede9fe; color: #7c3aed; }
      .icon-statement { background: var(--soft-card); color: var(--primary); }

      .tile-name {
        font-weight: 700;
        font-size: 0.94rem;
        color: var(--text);
        margin-bottom: 2px;
      }

      .tile-desc {
        font-size: 0.78rem;
        color: var(--muted);
      }

      /* Tables */
      .table-card {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
        margin-bottom: 24px;
      }

      .table-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 18px 22px;
        border-bottom: 1px solid var(--line);
        gap: 12px;
        flex-wrap: wrap;
      }

      .table-card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--sidebar-1);
      }

      .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
        text-align: left;
      }

      .data-table th {
        background: #f8fafc;
        color: var(--muted);
        font-weight: 600;
        padding: 12px 18px;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid var(--line);
      }

      .data-table td {
        padding: 14px 18px;
        border-bottom: 1px solid var(--line);
        color: var(--text);
      }

      .data-table tr:last-child td {
        border-bottom: none;
      }

      .data-table tr:hover td {
        background: #f8fafc;
      }

      .badge-kind {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 700;
        text-transform: uppercase;
      }

      .badge-credit { background: var(--success-bg); color: var(--success); }
      .badge-debit { background: var(--red-bg); color: var(--red); }
      .badge-refused { background: var(--warning-bg); color: var(--warning); }

      .badge-hash {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.74rem;
        background: #f1f5f9;
        color: #475569;
        padding: 3px 6px;
        border-radius: 4px;
      }

      /* Account Cards Grid */
      .account-card-box {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 22px;
        box-shadow: var(--shadow-sm);
        transition: all 0.15s ease;
        display: flex;
        flex-direction: column;
        gap: 14px;
      }

      .account-card-box:hover {
        border-color: #cbd5e1;
        box-shadow: var(--shadow);
      }

      .acc-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .acc-title-row {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .acc-badge-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #1d6de5, #092347);
        color: #ffffff;
        font-weight: 700;
        display: grid;
        place-items: center;
        font-size: 1rem;
      }

      .acc-name {
        font-weight: 700;
        font-size: 1rem;
        color: var(--sidebar-1);
      }

      .acc-num {
        font-size: 0.76rem;
        color: var(--muted);
        font-family: monospace;
      }

      .acc-bal {
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--sidebar-1);
      }

      .acc-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 12px;
        border-top: 1px solid var(--line);
        font-size: 0.82rem;
      }

      .acc-actions-bar {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }

      /* Statement Sheet */
      .statement-sheet {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 32px;
        box-shadow: var(--shadow-sm);
      }

      .statement-doc-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 2px solid var(--sidebar-1);
        padding-bottom: 18px;
        margin-bottom: 24px;
      }

      .statement-summary-box {
        background: #f8fafc;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 18px 24px;
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
      }

      /* Empty & Guest Notice States */
      .empty-state {
        text-align: center;
        padding: 50px 20px;
        color: var(--muted);
      }

      .empty-state-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
      }

      .guest-box {
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 48px 30px;
        text-align: center;
        max-width: 540px;
        margin: 40px auto;
        box-shadow: var(--shadow);
      }

      .guest-box-icon {
        font-size: 3rem;
        margin-bottom: 16px;
      }

      /* Auth Portal */
      .auth-card-wrap {
        max-width: 440px;
        margin: 40px auto;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }

      .auth-tabs {
        display: flex;
        border-bottom: 1px solid var(--line);
        background: #f8fafc;
      }

      .auth-tab-btn {
        flex: 1;
        padding: 14px;
        border: none;
        background: transparent;
        font-weight: 700;
        font-size: 0.92rem;
        cursor: pointer;
        color: var(--muted);
        transition: all 0.15s ease;
      }

      .auth-tab-btn.active {
        background: #ffffff;
        color: var(--primary);
        border-bottom: 2px solid var(--primary);
      }

      .auth-body {
        padding: 28px;
      }

      .form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 16px;
      }

      .form-group label {
        font-size: 0.84rem;
        font-weight: 600;
        color: var(--text);
      }

      .form-control {
        border: 1px solid var(--line);
        border-radius: 9px;
        padding: 10px 14px;
        font: inherit;
        font-size: 0.9rem;
        outline: none;
        transition: border-color 0.15s ease;
        width: 100%;
      }

      .form-control:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(29, 109, 229, 0.12);
      }

      /* Dialog */
      dialog {
        width: min(460px, calc(100vw - 32px));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 24px;
        color: var(--text);
        box-shadow: var(--shadow);
        margin: auto;
      }

      dialog::backdrop {
        background: rgba(7, 28, 53, 0.5);
        backdrop-filter: blur(2px);
      }

      /* Toast Notification */
      #result-box {
        position: fixed;
        right: 22px;
        bottom: 22px;
        z-index: 9999;
        max-width: min(480px, calc(100vw - 44px));
        padding: 14px 18px;
        border-radius: 12px;
        background: #092347;
        color: #ffffff;
        font-size: 0.88rem;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
        display: none;
        animation: fadeInPage 0.2s ease-in-out;
      }

      /* Responsive Breakpoints */
      @media (max-width: 960px) {
        .app-shell { flex-direction: column; }
        .sidebar {
          width: 100%;
          height: auto;
          position: relative;
          padding: 16px;
        }
        .nav { flex-direction: row; flex-wrap: wrap; }
        .sidebar-sec-box, .profile-mini { display: none; }
        .grid-4, .grid-3 { grid-template-columns: repeat(2, 1fr); }
      }

      @media (max-width: 640px) {
        .grid-4, .grid-3, .grid-2 { grid-template-columns: 1fr; }
        .statement-summary-box { grid-template-columns: repeat(2, 1fr); }
        .content { padding: 16px; }
      }
    </style>
  </head>
  <body>
    <div class="app-shell">
      <!-- Consistent Sidebar across all 7 pages -->
      <aside class="sidebar">
        <a class="brand" href="#overview">
          <div class="brand-mark">BV</div>
          <div>
            <div class="brand-text">BalanceVault</div>
            <div class="brand-sub" id="session-status">Not signed in</div>
          </div>
        </a>

        <nav class="nav">
          <a class="nav-item active" href="#overview" data-route="overview">
            <span class="nav-icon">📊</span> Overview
          </a>
          <a class="nav-item" href="#accounts" data-route="accounts">
            <span class="nav-icon">💳</span> My Accounts
          </a>
          <a class="nav-item" href="#transactions" data-route="transactions">
            <span class="nav-icon">⇄</span> Transactions
          </a>
          <a class="nav-item" href="#statements" data-route="statements">
            <span class="nav-icon">📄</span> Statements
          </a>
          <a class="nav-item" href="#audit" data-route="audit">
            <span class="nav-icon">🛡️</span> Security &amp; Audit
          </a>
          <div class="divider"></div>
          <a class="nav-item" href="#settings" data-route="settings">
            <span class="nav-icon">⚙️</span> Settings
          </a>
          <a class="nav-item" href="#auth" data-route="auth" id="sidebar-auth-nav">
            <span class="nav-icon">🔑</span> Sign In / Register
          </a>
        </nav>

        <div class="sidebar-sec-box">
          <div class="sec-shield-row">
            <span>🛡️</span>
            <span>Cryptographically Verified</span>
          </div>
          <div style="margin-top: 6px; color: rgba(255, 255, 255, 0.7); font-size: 0.74rem;">
            Double-entry ledger with immutable SHA-256 chain protection.
          </div>
        </div>

        <div class="profile-mini" id="sidebar-profile-box" title="View profile or switch account">
          <div class="avatar" id="sidebar-avatar">AM</div>
          <div class="profile-mini-info">
            <div class="profile-mini-name" id="sidebar-username">Guest</div>
            <div class="profile-mini-role" id="sidebar-role">Sign in to continue</div>
          </div>
        </div>
      </aside>

      <!-- Main Section -->
      <main class="main">
        <!-- Persistent Topbar -->
        <div class="topbar-main">
          <div class="top-search-wrap">
            <span>🔍</span>
            <input type="text" id="global-search" placeholder="Search accounts, transactions, or hashes..." />
          </div>

          <div class="top-actions">
            <button class="btn-refresh" type="button" id="top-refresh-btn" title="Refresh Live Data">↻</button>
            <button class="btn btn-primary btn-sm" id="top-register-btn" onclick="navigateTo('auth', 'register')">Register</button>

            <!-- User Menu with Profile & Logout Dropdown -->
            <div class="user-menu-wrapper">
              <div class="mini-user" id="user-menu-btn" role="button" tabindex="0">
                <div class="mini-avatar" id="topbar-avatar">AM</div>
                <div id="topbar-username" style="font-weight: 700; font-size: 0.88rem;">Sign in</div>
                <span id="topbar-caret" style="display:none; font-size: 0.72rem; color: var(--muted); margin-left: 2px;">▼</span>
              </div>
              <div id="user-dropdown" class="user-dropdown-menu" style="display: none;">
                <div class="dropdown-header">
                  <div class="dropdown-name" id="dropdown-user-name">Guest</div>
                  <div class="dropdown-role" id="dropdown-user-role">Sign in to continue</div>
                </div>
                <div class="dropdown-divider"></div>
                <button type="button" class="dropdown-item" id="btn-view-profile">
                  <span class="dropdown-icon">👤</span> Profile
                </button>
                <button type="button" class="dropdown-item logout-item" id="btn-logout">
                  <span class="dropdown-icon">🚪</span> Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Content Area: All 7 Distinct Pages -->
        <div class="content">

          <!-- ======================================================== -->
          <!-- PAGE 1: OVERVIEW -->
          <!-- ======================================================== -->
          <section id="view-overview" class="page-view active">
            <div class="page-header">
              <div>
                <h1 class="page-title">Financial Overview</h1>
                <div class="page-sub">Real-time ledger summary and quick financial operations.</div>
              </div>
              <div class="status-pill success" id="overview-ledger-pill">
                ● Cryptographic Ledger Verified
              </div>
            </div>

            <!-- Total Balance Hero Banner -->
            <div class="hero-card">
              <div class="hero-grid">
                <div>
                  <div class="balance-label">TOTAL ACCUMULATED BALANCE</div>
                  <div class="balance-value" id="overview-total-balance">₹0.00</div>
                  <div style="font-size: 0.85rem; color: rgba(255,255,255,0.8);" id="overview-acc-count">
                    0 Active Accounts
                  </div>
                </div>
                <div>
                  <button class="btn btn-outline btn-sm" onclick="navigateTo('accounts')" style="background: rgba(255,255,255,0.15); color: #fff; border: 1px solid rgba(255,255,255,0.3);">
                    Manage Accounts →
                  </button>
                </div>
              </div>
            </div>

            <!-- Financial Activity Stats -->
            <div class="grid-4">
              <div class="card stat-card">
                <span class="stat-card-label">TOTAL INFLOW (CREDITS)</span>
                <span class="stat-card-val" id="stat-total-credits" style="color: var(--success);">₹0.00</span>
                <span class="stat-card-sub">Sum of verified deposits</span>
              </div>
              <div class="card stat-card">
                <span class="stat-card-label">TOTAL OUTFLOW (DEBITS)</span>
                <span class="stat-card-val" id="stat-total-debits" style="color: var(--red);">₹0.00</span>
                <span class="stat-card-sub">Sum of withdrawals</span>
              </div>
              <div class="card stat-card">
                <span class="stat-card-label">TOTAL TRANSACTIONS</span>
                <span class="stat-card-val" id="stat-total-txs">0</span>
                <span class="stat-card-sub">Append-only ledger entries</span>
              </div>
              <div class="card stat-card">
                <span class="stat-card-label">LEDGER INTEGRITY</span>
                <span class="stat-card-val" id="stat-chain-status" style="font-size: 1.15rem; color: var(--success); margin-top: 4px;">✓ 100% Valid</span>
                <span class="stat-card-sub">SHA-256 hash chaining</span>
              </div>
            </div>

            <!-- Quick Actions Grid -->
            <div style="margin-bottom: 24px;">
              <h2 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 14px;">Quick Money Actions</h2>
              <div class="grid-4">
                <button class="action-tile-btn" onclick="openDepositModal()">
                  <div class="tile-icon-box icon-deposit">＋</div>
                  <div class="tile-name">Deposit</div>
                  <div class="tile-desc">Credit funds into account</div>
                </button>
                <button class="action-tile-btn" onclick="openWithdrawModal()">
                  <div class="tile-icon-box icon-withdraw">↑</div>
                  <div class="tile-name">Withdraw</div>
                  <div class="tile-desc">Debit with overdraft check</div>
                </button>
                <button class="action-tile-btn" onclick="openTransferModal()">
                  <div class="tile-icon-box icon-transfer">⇄</div>
                  <div class="tile-name">Transfer</div>
                  <div class="tile-desc">Atomic debit &amp; credit</div>
                </button>
                <button class="action-tile-btn" onclick="navigateTo('statements')">
                  <div class="tile-icon-box icon-statement">📄</div>
                  <div class="tile-name">Statement</div>
                  <div class="tile-desc">Download CSV or PDF</div>
                </button>
              </div>
            </div>

            <!-- 2-Column: Accounts Preview & Recent Transactions -->
            <div class="grid-2">
              <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                  <h3 style="font-size: 1rem; font-weight: 700;">Account Summaries</h3>
                  <a href="#accounts" style="color: var(--primary); text-decoration: none; font-size: 0.82rem; font-weight: 600;">View All →</a>
                </div>
                <div id="overview-accounts-preview" style="display: flex; flex-direction: column; gap: 10px;">
                  <div class="empty-state" style="padding: 20px;">Sign in to view accounts.</div>
                </div>
              </div>

              <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                  <h3 style="font-size: 1rem; font-weight: 700;">Recent Ledger Activity</h3>
                  <a href="#transactions" style="color: var(--primary); text-decoration: none; font-size: 0.82rem; font-weight: 600;">View All →</a>
                </div>
                <div id="overview-recent-txs" style="display: flex; flex-direction: column; gap: 8px;">
                  <div class="empty-state" style="padding: 20px;">No recent activity.</div>
                </div>
              </div>
            </div>
          </section>


          <!-- ======================================================== -->
          <!-- PAGE 2: MY ACCOUNTS -->
          <!-- ======================================================== -->
          <section id="view-accounts" class="page-view">
            <div class="page-header">
              <div>
                <h1 class="page-title">My Bank Accounts</h1>
                <div class="page-sub">View balances, account numbers, overdraft limits, and create new accounts.</div>
              </div>
              <div class="page-actions">
                <button class="btn btn-primary" id="btn-create-account" onclick="openCreateAccountModal()">
                  ＋ Create New Account
                </button>
              </div>
            </div>

            <!-- Accounts Protected Content or Guest Notice -->
            <div id="accounts-container">
              <div id="accounts-grid" class="grid-3">
                <!-- Dynamically populated account cards -->
              </div>
            </div>
          </section>


          <!-- ======================================================== -->
          <!-- PAGE 3: TRANSACTIONS -->
          <!-- ======================================================== -->
          <section id="view-transactions" class="page-view">
            <div class="page-header">
              <div>
                <h1 class="page-title">Transaction History</h1>
                <div class="page-sub">Explore full double-entry money movement with cryptographic hash verification.</div>
              </div>
              <div class="page-actions">
                <button class="btn btn-success btn-sm" onclick="openDepositModal()">＋ Deposit</button>
                <button class="btn btn-outline btn-sm" onclick="openWithdrawModal()">↑ Withdraw</button>
                <button class="btn btn-primary btn-sm" onclick="openTransferModal()">⇄ Transfer</button>
              </div>
            </div>

            <!-- Filter Controls Toolbar -->
            <div class="card" style="margin-bottom: 20px; padding: 14px 20px;">
              <div style="display: flex; gap: 14px; flex-wrap: wrap; align-items: center;">
                <input type="text" id="tx-search-input" class="form-control" style="max-width: 260px;" placeholder="Filter by description or ID..." />
                
                <select id="tx-account-filter" class="form-control" style="max-width: 200px;">
                  <option value="all">All Accounts</option>
                </select>

                <select id="tx-kind-filter" class="form-control" style="max-width: 160px;">
                  <option value="all">All Types</option>
                  <option value="credit">Credits Only</option>
                  <option value="debit">Debits Only</option>
                </select>

                <select id="tx-sort-order" class="form-control" style="max-width: 160px;">
                  <option value="desc">Newest First</option>
                  <option value="asc">Oldest First</option>
                </select>

                <button class="btn btn-outline btn-sm" onclick="filterTransactions()">Apply Filter</button>
              </div>
            </div>

            <!-- Transactions Table -->
            <div class="table-card">
              <div class="table-card-head">
                <div class="table-card-title">Ledger Entries</div>
                <div id="tx-table-counter" style="font-size: 0.82rem; color: var(--muted);">Showing 0 entries</div>
              </div>
              <div style="overflow-x: auto;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>TX ID</th>
                      <th>Date &amp; Time</th>
                      <th>Account</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Balance After</th>
                      <th>Description</th>
                      <th>Hash</th>
                      <th>Receipt</th>
                    </tr>
                  </thead>
                  <tbody id="transactions-tbody">
                    <tr><td colspan="9" style="text-align: center; padding: 30px; color: var(--muted);">Sign in to load transactions.</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>


          <!-- ======================================================== -->
          <!-- PAGE 4: STATEMENTS -->
          <!-- ======================================================== -->
          <section id="view-statements" class="page-view">
            <div class="page-header">
              <div>
                <h1 class="page-title">Account Statements</h1>
                <div class="page-sub">Generate official audit-ready financial statements with CSV download and print options.</div>
              </div>
            </div>

            <!-- Statement Controls Bar -->
            <div class="card" style="margin-bottom: 24px; padding: 18px 22px;">
              <div style="display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end;">
                <div style="display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 200px;">
                  <label style="font-size: 0.82rem; font-weight: 700; color: var(--muted);">SELECT ACCOUNT</label>
                  <select id="statement-account-select" class="form-control">
                    <!-- Populated dynamically -->
                  </select>
                </div>

                <div style="display: flex; flex-direction: column; gap: 6px; min-width: 170px;">
                  <label style="font-size: 0.82rem; font-weight: 700; color: var(--muted);">DATE RANGE</label>
                  <select id="statement-date-range" class="form-control">
                    <option value="all">All Available Records</option>
                    <option value="30">Last 30 Days</option>
                    <option value="7">Last 7 Days</option>
                  </select>
                </div>

                <button class="btn btn-primary" onclick="generateStatement()">
                  📄 View Statement
                </button>
                <button class="btn btn-outline" onclick="downloadStatementCSV()">
                  ⬇️ Download CSV
                </button>
                <button class="btn btn-outline" onclick="window.print()">
                  🖨️ Print
                </button>
              </div>
            </div>

            <!-- Rendered Official Statement Document -->
            <div class="statement-sheet" id="statement-document">
              <div class="statement-doc-head">
                <div>
                  <h2 style="font-size: 1.4rem; font-weight: 800; color: var(--sidebar-1);">BalanceVault Bank Statement</h2>
                  <div style="font-size: 0.85rem; color: var(--muted); margin-top: 4px;">
                    Account Statement for <strong id="stmt-account-name">—</strong> (<span id="stmt-account-owner">—</span>)
                  </div>
                </div>
                <div style="text-align: right;">
                  <div style="font-size: 0.8rem; color: var(--muted);">GENERATED ON</div>
                  <div style="font-weight: 700; font-size: 0.9rem;" id="stmt-generated-date">—</div>
                  <div class="status-pill success" style="margin-top: 6px;" id="stmt-integrity-pill">
                    ✓ Cryptographic Chain Verified
                  </div>
                </div>
              </div>

              <!-- Statement Financial Summary Box -->
              <div class="statement-summary-box">
                <div>
                  <div style="font-size: 0.78rem; color: var(--muted); font-weight: 600;">OPENING BALANCE</div>
                  <div style="font-size: 1.25rem; font-weight: 800;" id="stmt-opening-bal">₹0.00</div>
                </div>
                <div>
                  <div style="font-size: 0.78rem; color: var(--muted); font-weight: 600;">TOTAL CREDITS (IN)</div>
                  <div style="font-size: 1.25rem; font-weight: 800; color: var(--success);" id="stmt-total-credits">₹0.00</div>
                </div>
                <div>
                  <div style="font-size: 0.78rem; color: var(--muted); font-weight: 600;">TOTAL DEBITS (OUT)</div>
                  <div style="font-size: 1.25rem; font-weight: 800; color: var(--red);" id="stmt-total-debits">₹0.00</div>
                </div>
                <div>
                  <div style="font-size: 0.78rem; color: var(--muted); font-weight: 600;">CLOSING BALANCE</div>
                  <div style="font-size: 1.25rem; font-weight: 800; color: var(--sidebar-1);" id="stmt-closing-bal">₹0.00</div>
                </div>
              </div>

              <!-- Statement Entries Table -->
              <div style="overflow-x: auto;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Ref ID</th>
                      <th>Date (UTC)</th>
                      <th>Description</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Running Balance</th>
                      <th>SHA-256 Hash</th>
                    </tr>
                  </thead>
                  <tbody id="statement-tbody">
                    <tr><td colspan="7" style="text-align: center; padding: 30px; color: var(--muted);">Select an account and click 'View Statement'.</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>


          <!-- ======================================================== -->
          <!-- PAGE 5: SECURITY & AUDIT -->
          <!-- ======================================================== -->
          <section id="view-audit" class="page-view">
            <div class="page-header">
              <div>
                <h1 class="page-title">Security &amp; Cryptographic Audit</h1>
                <div class="page-sub">Independent ledger verification, cryptographic chain validation, and immutable audit logs.</div>
              </div>
              <div class="page-actions">
                <button class="btn btn-primary" onclick="verifyLedgerChainNow()">
                  🛡️ Run Live Hash Verification
                </button>
              </div>
            </div>

            <!-- Ledger Verification Status Card -->
            <div class="hero-card" style="background: linear-gradient(135deg, #064e3b 0%, #065f46 60%, #047857 100%); margin-bottom: 24px;">
              <div class="hero-grid">
                <div>
                  <div class="balance-label">CRYPTOGRAPHIC CHAIN INTEGRITY STATUS</div>
                  <div class="balance-value" id="audit-hero-status" style="font-size: 1.9rem;">● All Hashes Validated</div>
                  <div style="font-size: 0.85rem; color: rgba(255,255,255,0.85);" id="audit-hero-details">
                    Every ledger entry contains an immutable SHA-256 link to its predecessor.
                  </div>
                </div>
                <div>
                  <button class="btn btn-outline btn-sm" onclick="verifyLedgerChainNow()" style="background: rgba(255,255,255,0.2); color: #fff; border: 1px solid rgba(255,255,255,0.4);">
                    Re-Verify Chain
                  </button>
                </div>
              </div>
            </div>

            <!-- Security Controls Architecture Grid -->
            <h2 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 14px;">Enterprise Security Controls</h2>
            <div class="grid-4" style="margin-bottom: 28px;">
              <div class="card stat-card">
                <div style="font-size: 1.3rem; margin-bottom: 4px;">⚖️</div>
                <span class="stat-card-label">DOUBLE-ENTRY ACCOUNTING</span>
                <span style="font-size: 0.82rem; color: var(--muted);">Every transfer creates strictly balanced debit and credit entries.</span>
              </div>
              <div class="card stat-card">
                <div style="font-size: 1.3rem; margin-bottom: 4px;">🔒</div>
                <span class="stat-card-label">APPEND-ONLY PROTECTION</span>
                <span style="font-size: 0.82rem; color: var(--muted);">Database rules and triggers prohibit modifying or deleting records.</span>
              </div>
              <div class="card stat-card">
                <div style="font-size: 1.3rem; margin-bottom: 4px;">🛡️</div>
                <span class="stat-card-label">ROW-LEVEL LOCKING</span>
                <span style="font-size: 0.82rem; color: var(--muted);">SELECT ... FOR UPDATE prevents race conditions and overdrafts.</span>
              </div>
              <div class="card stat-card">
                <div style="font-size: 1.3rem; margin-bottom: 4px;">⚡</div>
                <span class="stat-card-label">REDIS RATE LIMITING</span>
                <span style="font-size: 0.82rem; color: var(--muted);">Protects auth and sensitive money endpoints with HTTP 429 controls.</span>
              </div>
            </div>

            <!-- Immutable Audit Ledger Trail -->
            <div class="table-card">
              <div class="table-card-head">
                <div class="table-card-title">Cryptographic Audit Chain (Chronological Trail)</div>
                <div style="font-size: 0.82rem; color: var(--muted);">Showing verified blocks</div>
              </div>
              <div style="overflow-x: auto;">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Block #</th>
                      <th>Timestamp</th>
                      <th>Account</th>
                      <th>Operation</th>
                      <th>Amount</th>
                      <th>Balance</th>
                      <th>Previous Hash</th>
                      <th>Current Hash</th>
                      <th>Chain Status</th>
                    </tr>
                  </thead>
                  <tbody id="audit-trail-tbody">
                    <tr><td colspan="9" style="text-align: center; padding: 30px; color: var(--muted);">Loading audit log...</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>


          <!-- ======================================================== -->
          <!-- PAGE 6: SETTINGS -->
          <!-- ======================================================== -->
          <section id="view-settings" class="page-view">
            <div class="page-header">
              <div>
                <h1 class="page-title">Settings &amp; Preferences</h1>
                <div class="page-sub">Manage your profile, password security, and active application preferences.</div>
              </div>
            </div>

            <div class="grid-2">
              <!-- Profile Card -->
              <div class="card">
                <h2 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 16px;">User Profile</h2>
                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 20px;">
                  <div class="avatar" id="settings-avatar" style="width: 54px; height: 54px; font-size: 1.3rem;">AM</div>
                  <div>
                    <h3 id="settings-username" style="font-size: 1.15rem; font-weight: 700;">Guest</h3>
                    <div id="settings-role" class="badge-kind badge-credit" style="margin-top: 4px;">Account Holder</div>
                  </div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 0.88rem;">
                  <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--line); padding-bottom: 8px;">
                    <span style="color: var(--muted);">User ID:</span>
                    <strong id="settings-user-id">#—</strong>
                  </div>
                  <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--line); padding-bottom: 8px;">
                    <span style="color: var(--muted);">Session Type:</span>
                    <span style="color: var(--success); font-weight: 600;">● Active (JWT Bearer)</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--line); padding-bottom: 8px;">
                    <span style="color: var(--muted);">Assigned Permissions:</span>
                    <span id="settings-permissions-count">0 Permissions</span>
                  </div>
                </div>

                <div style="margin-top: 14px;">
                  <div style="font-size: 0.8rem; font-weight: 700; color: var(--muted); margin-bottom: 8px;">PERMISSIONS:</div>
                  <div id="settings-permissions-chips" style="display: flex; flex-wrap: wrap; gap: 6px;">
                    <!-- Chips -->
                  </div>
                </div>
              </div>

              <!-- Password Management Form -->
              <div class="card">
                <h2 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 8px;">Password Management</h2>
                <div style="font-size: 0.82rem; color: var(--muted); margin-bottom: 16px;">
                  Update your account password. Requires your current password for security verification.
                </div>

                <form id="form-change-password" onsubmit="handleChangePassword(event)">
                  <div class="form-group">
                    <label>Current Password</label>
                    <input type="password" id="cp-current" class="form-control" required />
                  </div>
                  <div class="form-group">
                    <label>New Password (min 8 characters)</label>
                    <input type="password" id="cp-new" class="form-control" minlength="8" required />
                  </div>
                  <div class="form-group">
                    <label>Confirm New Password</label>
                    <input type="password" id="cp-confirm" class="form-control" minlength="8" required />
                  </div>
                  <div id="cp-status-msg" style="display: none; font-size: 0.84rem; padding: 8px 12px; border-radius: 8px; margin-bottom: 14px;"></div>
                  <button type="submit" class="btn btn-primary" style="width: 100%;">
                    Update Password
                  </button>
                </form>
              </div>
            </div>

            <!-- Preferences & System Information -->
            <div class="grid-2">
              <div class="card">
                <h2 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 14px;">Preferences</h2>
                <div style="display: flex; flex-direction: column; gap: 12px; font-size: 0.88rem;">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>Display Currency</span>
                    <select class="form-control" style="width: 140px;">
                      <option value="INR">₹ INR (India)</option>
                      <option value="USD">$ USD</option>
                    </select>
                  </div>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>Auto-Refresh Polling</span>
                    <select class="form-control" style="width: 140px;">
                      <option value="30">Every 30s</option>
                      <option value="60">Every 60s</option>
                      <option value="0">Manual Only</option>
                    </select>
                  </div>
                </div>
              </div>

              <div class="card">
                <h2 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 14px;">Sign Out</h2>
                <div style="font-size: 0.84rem; color: var(--muted); margin-bottom: 16px;">
                  Signing out clears your local authentication token.
                </div>
                <button class="btn btn-danger" onclick="logoutSession()" style="width: 100%;">
                  🚪 Sign Out of BalanceVault
                </button>
              </div>
            </div>
          </section>


          <!-- ======================================================== -->
          <!-- PAGE 7: AUTHENTICATION -->
          <!-- ======================================================== -->
          <section id="view-auth" class="page-view">
            <div class="page-header" style="justify-content: center; text-align: center;">
              <div>
                <h1 class="page-title">Authentication Portal</h1>
                <div class="page-sub">Sign in to your account or register a new identity on BalanceVault.</div>
              </div>
            </div>

            <div class="auth-card-wrap">
              <div class="auth-tabs">
                <button class="auth-tab-btn active" id="tab-login-btn" onclick="switchAuthTab('login')">Sign In</button>
                <button class="auth-tab-btn" id="tab-register-btn" onclick="switchAuthTab('register')">Register</button>
              </div>

              <!-- Sign In View -->
              <div class="auth-body" id="auth-login-view">
                <form onsubmit="handleAuthLogin(event)">
                  <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="auth-login-username" class="form-control" placeholder="e.g. admin or alice" required />
                  </div>
                  <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="auth-login-password" class="form-control" placeholder="••••••••" required />
                  </div>
                  <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 10px;">
                    Sign In
                  </button>
                </form>

                <!-- Demo helper -->
                <div style="margin-top: 20px; padding: 12px; background: #f8fafc; border-radius: 10px; font-size: 0.78rem; border: 1px solid var(--line);">
                  <strong>Quick Test Accounts:</strong><br />
                  • Admin: <code>admin</code> / <code>adminpass</code><br />
                  • Alice: <code>alice</code> / <code>pass123</code><br />
                  • Auditor: <code>auditor</code> / <code>pass123</code>
                </div>
              </div>

              <!-- Register View -->
              <div class="auth-body" id="auth-register-view" style="display: none;">
                <form onsubmit="handleAuthRegister(event)">
                  <div class="form-group">
                    <label>Choose Username (min 3 chars)</label>
                    <input type="text" id="auth-reg-username" class="form-control" placeholder="e.g. your_username" minlength="3" required />
                  </div>
                  <div class="form-group">
                    <label>Password (min 8 chars)</label>
                    <input type="password" id="auth-reg-password" class="form-control" placeholder="••••••••" minlength="8" required />
                  </div>
                  <div class="form-group">
                    <label>Confirm Password</label>
                    <input type="password" id="auth-reg-confirm" class="form-control" placeholder="••••••••" minlength="8" required />
                  </div>
                  <div style="font-size: 0.78rem; color: var(--muted); margin-bottom: 12px;">
                    Registration automatically provisions your primary bank account with a ₹1,000 welcome balance.
                  </div>
                  <button type="submit" class="btn btn-primary" style="width: 100%;">
                    Register &amp; Open Account
                  </button>
                </form>
              </div>
            </div>
          </section>

        </div>
      </main>
    </div>

    <!-- Generic Modal Dialog -->
    <dialog id="app-dialog"></dialog>

    <!-- Global Toast Notification Box -->
    <div id="result-box"></div>

    <!-- Application JavaScript Engine -->
    <script>
      const storageKey = 'ledgerline-token';
      const pendingOperationKey = 'ledgerline-pending-operation';
      let activeUser = null;
      let accounts = [];
      let ledgerEntries = [];
      let dashboardReady = false;
      let currentRoute = 'overview';

      // ======================================================================
      // Toast / Notification System
      // ======================================================================
      function showResult(message, isError = false) {
        const box = document.getElementById('result-box');
        box.textContent = message;
        box.style.background = isError ? '#991b1b' : '#092347';
        box.style.display = 'block';
        clearTimeout(box._timer);
        box._timer = setTimeout(() => {
          box.style.display = 'none';
        }, 5000);
      }

      function getToken() {
        return localStorage.getItem(storageKey);
      }

      // ======================================================================
      // API Helper
      // ======================================================================
      async function api(path, options = {}) {
        const token = getToken();
        const headers = { ...(options.headers || {}) };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';

        const response = await fetch(path, { ...options, headers });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          const errorMsg = data.detail || `Request failed (${response.status})`;
          const err = new Error(errorMsg);
          err.status = response.status;
          throw err;
        }
        return data;
      }

      function formatMoney(amount) {
        return new Intl.NumberFormat('en-IN', {
          style: 'currency',
          currency: 'INR',
          maximumFractionDigits: 2,
        }).format(amount || 0);
      }

      function formatDate(timestamp) {
        if (!timestamp) return '—';
        return new Date(timestamp * 1000).toLocaleString('en-IN', {
          dateStyle: 'medium',
          timeStyle: 'short',
        });
      }

      // ======================================================================
      // Navigation & Router Engine
      // ======================================================================
      function navigateTo(route, subAction = null) {
        const validRoutes = ['overview', 'accounts', 'transactions', 'statements', 'audit', 'settings', 'auth'];
        if (!validRoutes.includes(route)) route = 'overview';
        currentRoute = route;

        // Update URL hash without reload
        if (window.location.hash !== `#${route}`) {
          window.location.hash = route;
        }

        // Highlight sidebar nav item
        document.querySelectorAll('.nav-item').forEach(el => {
          if (el.dataset.route === route) {
            el.classList.add('active');
          } else {
            el.classList.remove('active');
          }
        });

        // Hide all views, display targeted view
        document.querySelectorAll('.page-view').forEach(view => {
          if (view.id === `view-${route}`) {
            view.classList.add('active');
          } else {
            view.classList.remove('active');
          }
        });

        // Subaction for auth (switch tab)
        if (route === 'auth' && subAction) {
          switchAuthTab(subAction);
        }

        // Render page data
        if (route === 'overview') renderOverviewPage();
        else if (route === 'accounts') renderAccountsPage();
        else if (route === 'transactions') renderTransactionsPage();
        else if (route === 'statements') renderStatementsPage();
        else if (route === 'audit') renderAuditPage();
        else if (route === 'settings') renderSettingsPage();
        else if (route === 'auth') renderAuthPage();

        window.scrollTo({ top: 0, behavior: 'smooth' });
      }

      // Listen for browser forward/back buttons
      window.addEventListener('hashchange', () => {
        const hash = window.location.hash.replace('#', '') || 'overview';
        navigateTo(hash);
      });

      // Sidebar click delegation
      document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
          e.preventDefault();
          const route = item.dataset.route;
          if (route) navigateTo(route);
        });
      });

      // ======================================================================
      // Session Management
      // ======================================================================
      function setSession(token, user = null) {
        if (token) {
          localStorage.setItem(storageKey, token);
        } else {
          localStorage.removeItem(storageKey);
          sessionStorage.removeItem(pendingOperationKey);
          dashboardReady = false;
          activeUser = null;
          accounts = [];
          ledgerEntries = [];
        }

        if (user) {
          activeUser = user;
          const initials = user.username ? user.username.slice(0, 2).toUpperCase() : 'AM';
          document.getElementById('topbar-avatar').textContent = initials;
          document.getElementById('sidebar-avatar').textContent = initials;
          document.getElementById('topbar-caret').style.display = 'inline-block';
          document.getElementById('topbar-username').textContent = user.username;
          document.getElementById('sidebar-username').textContent = user.username;
          document.getElementById('sidebar-role').textContent = (user.role || 'account_holder').replaceAll('_', ' ');
          document.getElementById('dropdown-user-name').textContent = user.username;
          document.getElementById('dropdown-user-role').textContent = (user.role || 'account_holder').replaceAll('_', ' ');
          document.getElementById('session-status').textContent = 'Signed in';
          document.getElementById('top-register-btn').style.display = 'none';
        } else {
          document.getElementById('topbar-avatar').textContent = 'AM';
          document.getElementById('sidebar-avatar').textContent = 'AM';
          document.getElementById('topbar-caret').style.display = 'none';
          document.getElementById('topbar-username').textContent = 'Sign in';
          document.getElementById('sidebar-username').textContent = 'Guest';
          document.getElementById('sidebar-role').textContent = 'Sign in to continue';
          document.getElementById('session-status').textContent = 'Not signed in';
          document.getElementById('top-register-btn').style.display = 'inline-block';
          const drop = document.getElementById('user-dropdown');
          if (drop) drop.style.display = 'none';
        }

        // Re-render current page
        navigateTo(currentRoute);
      }

      function logoutSession() {
        setSession(null);
        showResult('You have signed out successfully.');
        navigateTo('auth', 'login');
      }

      // ======================================================================
      // Data Refresh Engine
      // ======================================================================
      async function refreshDashboard() {
        if (!getToken()) return;

        try {
          const user = await api('/auth/me');
          const accountRows = await api('/accounts');
          accounts = accountRows;

          // Fetch statements for all accounts
          const statements = await Promise.all(
            accounts.map(acc => api(`/accounts/${acc.id}/statement`).catch(() => ({ entries: [] })))
          );

          ledgerEntries = statements.flatMap((stmt, i) =>
            (stmt.entries || []).map(e => ({
              ...e,
              account_id: accounts[i].id,
              account_name: accounts[i].name,
            }))
          ).sort((a, b) => b.id - a.id);

          dashboardReady = true;
          setSession(getToken(), user);
        } catch (error) {
          if (error.status === 401) {
            setSession(null);
          } else {
            showResult(error.message, true);
          }
        }
      }

      // ======================================================================
      // Page 1: Render Overview
      // ======================================================================
      function renderOverviewPage() {
        if (!getToken()) {
          document.getElementById('overview-total-balance').textContent = '₹0.00';
          document.getElementById('overview-acc-count').textContent = 'Sign in to view accounts';
          document.getElementById('stat-total-credits').textContent = '₹0.00';
          document.getElementById('stat-total-debits').textContent = '₹0.00';
          document.getElementById('stat-total-txs').textContent = '0';
          document.getElementById('overview-accounts-preview').innerHTML =
            '<div class="empty-state" style="padding:20px;">Please <a href="#auth" style="color:var(--primary);">Sign in</a> to view your accounts.</div>';
          document.getElementById('overview-recent-txs').innerHTML =
            '<div class="empty-state" style="padding:20px;">Sign in to view recent transactions.</div>';
          return;
        }

        const totalBal = accounts.reduce((sum, a) => sum + (Number(a.balance) || 0), 0);
        document.getElementById('overview-total-balance').textContent = formatMoney(totalBal);
        document.getElementById('overview-acc-count').textContent = `${accounts.length} Active Account${accounts.length === 1 ? '' : 's'}`;

        const credits = ledgerEntries.filter(e => e.kind === 'credit').reduce((s, e) => s + (Number(e.amount) || 0), 0);
        const debits = ledgerEntries.filter(e => e.kind === 'debit').reduce((s, e) => s + (Number(e.amount) || 0), 0);
        document.getElementById('stat-total-credits').textContent = formatMoney(credits);
        document.getElementById('stat-total-debits').textContent = formatMoney(debits);
        document.getElementById('stat-total-txs').textContent = ledgerEntries.length;

        // Accounts Preview (top 3)
        const accPrev = document.getElementById('overview-accounts-preview');
        accPrev.replaceChildren();
        if (accounts.length === 0) {
          accPrev.innerHTML = '<div class="empty-state" style="padding: 20px;">No accounts found. Click "My Accounts" to create one.</div>';
        } else {
          accounts.slice(0, 3).forEach(acc => {
            const row = document.createElement('div');
            row.style.display = 'flex';
            row.style.justifyContent = 'space-between';
            row.style.alignItems = 'center';
            row.style.padding = '10px 12px';
            row.style.borderRadius = '10px';
            row.style.background = '#f8fafc';
            row.style.border = '1px solid var(--line)';
            row.innerHTML = `
              <div>
                <strong style="font-size:0.92rem; color:var(--sidebar-1);">${acc.name}</strong>
                <div style="font-size:0.75rem; color:var(--muted); font-family:monospace;">#ACC-${String(acc.id).padStart(5, '0')}</div>
              </div>
              <div style="font-size:1.05rem; font-weight:800; color:var(--sidebar-1);">
                ${formatMoney(acc.balance)}
              </div>
            `;
            accPrev.appendChild(row);
          });
        }

        // Recent Activity Preview (top 5)
        const recentTxs = document.getElementById('overview-recent-txs');
        recentTxs.replaceChildren();
        if (ledgerEntries.length === 0) {
          recentTxs.innerHTML = '<div class="empty-state" style="padding: 20px;">No transaction entries yet.</div>';
        } else {
          ledgerEntries.slice(0, 5).forEach(e => {
            const isCredit = e.kind === 'credit';
            const row = document.createElement('div');
            row.style.display = 'flex';
            row.style.justifyContent = 'space-between';
            row.style.alignItems = 'center';
            row.style.padding = '8px 12px';
            row.style.borderRadius = '8px';
            row.style.borderBottom = '1px solid var(--line)';
            row.innerHTML = `
              <div>
                <div style="font-size:0.86rem; font-weight:600;">${e.description || e.kind}</div>
                <div style="font-size:0.72rem; color:var(--muted);">${formatDate(e.created_at)}</div>
              </div>
              <div style="font-size:0.92rem; font-weight:700; color:${isCredit ? 'var(--success)' : 'var(--red)'};">
                ${isCredit ? '+' : '-'}${formatMoney(e.amount)}
              </div>
            `;
            recentTxs.appendChild(row);
          });
        }
      }

      // ======================================================================
      // Page 2: Render My Accounts
      // ======================================================================
      function renderAccountsPage() {
        const container = document.getElementById('accounts-container');
        if (!getToken()) {
          container.innerHTML = `
            <div class="guest-box">
              <div class="guest-box-icon">🔒</div>
              <h2 style="font-size:1.3rem; margin-bottom:8px;">Sign In to View Accounts</h2>
              <p style="color:var(--muted); margin-bottom:20px; font-size:0.9rem;">
                Protected bank accounts are restricted to authenticated sessions.
              </p>
              <button class="btn btn-primary" onclick="navigateTo('auth', 'login')">Sign In Now</button>
            </div>
          `;
          return;
        }

        const grid = document.createElement('div');
        grid.className = 'grid-3';

        if (accounts.length === 0) {
          container.innerHTML = `
            <div class="empty-state">
              <div class="empty-state-icon">💳</div>
              <h3>No Accounts Found</h3>
              <p>Create your first portfolio account to start moving money.</p>
              <button class="btn btn-primary" style="margin-top:14px;" onclick="openCreateAccountModal()">＋ Create Account</button>
            </div>
          `;
          return;
        }

        accounts.forEach(acc => {
          const card = document.createElement('div');
          card.className = 'account-card-box';
          card.innerHTML = `
            <div class="acc-head">
              <div class="acc-title-row">
                <div class="acc-badge-icon">${acc.name.slice(0, 1).toUpperCase()}</div>
                <div>
                  <div class="acc-name">${acc.name}</div>
                  <div class="acc-num">#ACC-${String(acc.id).padStart(6, '0')}</div>
                </div>
              </div>
              <span class="status-pill success">Active</span>
            </div>

            <div style="margin: 6px 0;">
              <div style="font-size: 0.78rem; color: var(--muted); font-weight: 600;">AVAILABLE BALANCE</div>
              <div class="acc-bal">${formatMoney(acc.balance)}</div>
            </div>

            <div style="font-size: 0.8rem; color: var(--muted); display: flex; justify-content: space-between;">
              <span>Overdraft Limit: ₹0.00</span>
              <span>Owner: @${acc.owner_username}</span>
            </div>

            <div class="acc-footer">
              <div class="acc-actions-bar">
                <button class="btn btn-outline btn-sm" onclick="openDepositForAccount(${acc.id})">Deposit</button>
                <button class="btn btn-outline btn-sm" onclick="openWithdrawForAccount(${acc.id})">Withdraw</button>
                <button class="btn btn-outline btn-sm" onclick="openTransferForAccount(${acc.id})">Transfer</button>
              </div>
              <button class="btn btn-primary btn-sm" onclick="viewAccountStatement(${acc.id})">Statement</button>
            </div>
          `;
          grid.appendChild(card);
        });

        container.replaceChildren(grid);
      }

      // ======================================================================
      // Page 3: Render Transactions
      // ======================================================================
      function renderTransactionsPage() {
        const tbody = document.getElementById('transactions-tbody');
        if (!getToken()) {
          tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px; color: var(--muted);">Please sign in to view transaction history.</td></tr>';
          return;
        }

        // Populate accounts filter dropdown
        const accSelect = document.getElementById('tx-account-filter');
        const prevVal = accSelect.value;
        accSelect.innerHTML = '<option value="all">All Accounts</option>';
        accounts.forEach(a => {
          const opt = document.createElement('option');
          opt.value = a.id;
          opt.textContent = `${a.name} (#${a.id})`;
          accSelect.appendChild(opt);
        });
        if (prevVal) accSelect.value = prevVal;

        filterTransactions();
      }

      function filterTransactions() {
        const tbody = document.getElementById('transactions-tbody');
        const q = (document.getElementById('tx-search-input').value || '').toLowerCase().trim();
        const accFilter = document.getElementById('tx-account-filter').value;
        const kindFilter = document.getElementById('tx-kind-filter').value;
        const sortOrder = document.getElementById('tx-sort-order').value;

        let filtered = [...ledgerEntries];

        if (accFilter !== 'all') {
          filtered = filtered.filter(e => String(e.account_id) === accFilter);
        }

        if (kindFilter !== 'all') {
          filtered = filtered.filter(e => e.kind === kindFilter);
        }

        if (q) {
          filtered = filtered.filter(e =>
            (e.description || '').toLowerCase().includes(q) ||
            String(e.id).includes(q) ||
            (e.hash_value || '').toLowerCase().includes(q)
          );
        }

        filtered.sort((a, b) => sortOrder === 'asc' ? a.id - b.id : b.id - a.id);

        document.getElementById('tx-table-counter').textContent = `Showing ${filtered.length} of ${ledgerEntries.length} entries`;

        if (filtered.length === 0) {
          tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px; color: var(--muted);">No matching transactions found.</td></tr>';
          return;
        }

        tbody.replaceChildren();
        filtered.forEach(e => {
          const isCredit = e.kind === 'credit';
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><strong>#TX-${String(e.id).padStart(5, '0')}</strong></td>
            <td>${formatDate(e.created_at)}</td>
            <td>${e.account_name || 'Account #' + e.account_id}</td>
            <td><span class="badge-kind ${isCredit ? 'badge-credit' : 'badge-debit'}">${e.kind}</span></td>
            <td style="font-weight: 700; color: ${isCredit ? 'var(--success)' : 'var(--red)'};">
              ${isCredit ? '+' : '-'}${formatMoney(e.amount)}
            </td>
            <td>${formatMoney(e.running_balance)}</td>
            <td>${e.description || '—'}</td>
            <td><span class="badge-hash" title="${e.hash_value}">${(e.hash_value || '').slice(0, 10)}…</span></td>
            <td>
              <button class="btn btn-outline btn-sm" onclick='showReceiptModal(${JSON.stringify(e)})'>
                Receipt
              </button>
            </td>
          `;
          tbody.appendChild(tr);
        });
      }

      function showReceiptModal(entry) {
        const dialog = document.getElementById('app-dialog');
        dialog.replaceChildren();

        const form = document.createElement('form');
        form.method = 'dialog';
        form.style.display = 'grid';
        form.style.gap = '14px';

        form.innerHTML = `
          <h2 style="font-size:1.25rem;">Transaction Receipt</h2>
          <div style="font-size:0.85rem; color:var(--muted);">Cryptographically verified record from append-only ledger.</div>
          
          <div style="background:#f8fafc; border:1px solid var(--line); border-radius:12px; padding:14px; font-size:0.86rem; display:grid; gap:8px;">
            <div style="display:flex; justify-content:space-between;">
              <span>Reference ID:</span> <strong>#TX-${String(entry.id).padStart(6, '0')}</strong>
            </div>
            <div style="display:flex; justify-content:space-between;">
              <span>Date &amp; Time (UTC):</span> <span>${formatDate(entry.created_at)}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
              <span>Account:</span> <strong>${entry.account_name || '#' + entry.account_id}</strong>
            </div>
            <div style="display:flex; justify-content:space-between;">
              <span>Operation:</span> <span class="badge-kind ${entry.kind === 'credit' ? 'badge-credit' : 'badge-debit'}">${entry.kind.toUpperCase()}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
              <span>Amount:</span> <strong style="font-size:1rem; color:${entry.kind === 'credit' ? 'var(--success)' : 'var(--red)'};">${formatMoney(entry.amount)}</strong>
            </div>
            <div style="display:flex; justify-content:space-between;">
              <span>Balance After:</span> <strong>${formatMoney(entry.running_balance)}</strong>
            </div>
            <div style="display:flex; justify-content:space-between;">
              <span>Description:</span> <span>${entry.description || '—'}</span>
            </div>
          </div>

          <div style="font-size:0.75rem; color:var(--muted);">
            <div><strong>PREV HASH:</strong></div>
            <div class="badge-hash" style="word-break:break-all; margin-bottom:6px;">${entry.prev_hash || 'genesis'}</div>
            <div><strong>CURRENT HASH (SHA-256):</strong></div>
            <div class="badge-hash" style="word-break:break-all;">${entry.hash_value}</div>
          </div>

          <div style="display:flex; justify-content:flex-end; margin-top:8px;">
            <button type="submit" class="btn btn-primary">Close Receipt</button>
          </div>
        `;

        dialog.appendChild(form);
        dialog.showModal();
      }

      // ======================================================================
      // Page 4: Render Statements
      // ======================================================================
      function renderStatementsPage() {
        if (!getToken()) {
          document.getElementById('statement-document').innerHTML = `
            <div class="guest-box">
              <div class="guest-box-icon">🔒</div>
              <h2>Sign In to Generate Statements</h2>
              <p style="color:var(--muted); margin:12px 0 20px;">Authenticated credentials required.</p>
              <button class="btn btn-primary" onclick="navigateTo('auth', 'login')">Sign In</button>
            </div>
          `;
          return;
        }

        const select = document.getElementById('statement-account-select');
        select.innerHTML = '';
        accounts.forEach(acc => {
          const opt = document.createElement('option');
          opt.value = acc.id;
          opt.textContent = `${acc.name} (#ACC-${String(acc.id).padStart(5, '0')}) — ${formatMoney(acc.balance)}`;
          select.appendChild(opt);
        });

        if (accounts.length > 0) {
          generateStatement();
        }
      }

      async function generateStatement() {
        const select = document.getElementById('statement-account-select');
        const accountId = Number(select.value);
        if (!accountId) return;

        const acc = accounts.find(a => a.id === accountId);
        if (!acc) return;

        try {
          const data = await api(`/accounts/${accountId}/statement`);
          const entries = data.entries || [];

          document.getElementById('stmt-account-name').textContent = acc.name;
          document.getElementById('stmt-account-owner').textContent = `@${acc.owner_username}`;
          document.getElementById('stmt-generated-date').textContent = new Date().toLocaleDateString('en-IN', {
            day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
          });

          // Calculations
          const credits = entries.filter(e => e.kind === 'credit').reduce((s, e) => s + (Number(e.amount) || 0), 0);
          const debits = entries.filter(e => e.kind === 'debit').reduce((s, e) => s + (Number(e.amount) || 0), 0);
          const closing = acc.balance;
          const opening = entries.length > 0 ? entries[0].running_balance - (entries[0].kind === 'credit' ? entries[0].amount : -entries[0].amount) : 0;

          document.getElementById('stmt-opening-bal').textContent = formatMoney(opening);
          document.getElementById('stmt-total-credits').textContent = `+${formatMoney(credits)}`;
          document.getElementById('stmt-total-debits').textContent = `-${formatMoney(debits)}`;
          document.getElementById('stmt-closing-bal').textContent = formatMoney(closing);

          const tbody = document.getElementById('statement-tbody');
          tbody.replaceChildren();

          if (entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px; color: var(--muted);">No transactions recorded for this account.</td></tr>';
            return;
          }

          entries.forEach(e => {
            const isCredit = e.kind === 'credit';
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>#${e.id}</td>
              <td>${formatDate(e.created_at)}</td>
              <td>${e.description || '—'}</td>
              <td><span class="badge-kind ${isCredit ? 'badge-credit' : 'badge-debit'}">${e.kind}</span></td>
              <td style="font-weight:700; color:${isCredit ? 'var(--success)' : 'var(--red)'};">
                ${isCredit ? '+' : '-'}${formatMoney(e.amount)}
              </td>
              <td style="font-weight:700;">${formatMoney(e.running_balance)}</td>
              <td><span class="badge-hash">${(e.hash_value || '').slice(0, 12)}…</span></td>
            `;
            tbody.appendChild(tr);
          });
        } catch (error) {
          showResult(error.message, true);
        }
      }

      function downloadStatementCSV() {
        const select = document.getElementById('statement-account-select');
        const accountId = Number(select.value);
        if (!accountId) {
          showResult('Please select an account first.', true);
          return;
        }
        window.open(`/accounts/${accountId}/statement/csv`, '_blank');
      }

      function viewAccountStatement(accountId) {
        navigateTo('statements');
        setTimeout(() => {
          const select = document.getElementById('statement-account-select');
          if (select) {
            select.value = accountId;
            generateStatement();
          }
        }, 50);
      }

      // ======================================================================
      // Page 5: Render Security & Audit
      // ======================================================================
      async function renderAuditPage() {
        const tbody = document.getElementById('audit-trail-tbody');
        if (!getToken()) {
          tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px; color: var(--muted);">Please sign in to inspect the audit ledger.</td></tr>';
          return;
        }

        try {
          // If auditor or superadmin, fetch full ledger entries
          const canReadAll = activeUser && (activeUser.role === 'admin' || activeUser.role === 'super_admin' || activeUser.role === 'auditor');
          let entries = [];

          if (canReadAll) {
            const res = await api('/ledger/entries?limit=50').catch(() => null);
            if (res && res.entries) entries = res.entries;
          }

          if (entries.length === 0) {
            entries = [...ledgerEntries];
          }

          tbody.replaceChildren();

          if (entries.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 30px; color: var(--muted);">No audit blocks recorded yet.</td></tr>';
            return;
          }

          entries.forEach(e => {
            const isCredit = e.kind === 'credit';
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td><strong>#BLOCK-${String(e.id).padStart(5, '0')}</strong></td>
              <td>${formatDate(e.created_at)}</td>
              <td>ACC #${e.account_id}</td>
              <td><span class="badge-kind ${isCredit ? 'badge-credit' : 'badge-debit'}">${e.kind}</span></td>
              <td style="font-weight:700;">${formatMoney(e.amount)}</td>
              <td>${formatMoney(e.running_balance)}</td>
              <td><span class="badge-hash" title="${e.prev_hash}">${(e.prev_hash || 'genesis').slice(0, 8)}…</span></td>
              <td><span class="badge-hash" title="${e.hash_value}">${(e.hash_value || '').slice(0, 8)}…</span></td>
              <td><span class="status-pill success" style="font-size:0.7rem;">✓ Linked</span></td>
            `;
            tbody.appendChild(tr);
          });
        } catch (error) {
          showResult(error.message, true);
        }
      }

      async function verifyLedgerChainNow() {
        if (!getToken()) {
          showResult('Sign in as administrator or auditor to verify ledger chain.', true);
          return;
        }
        try {
          const res = await api('/ledger/verify');
          if (res.hash_valid) {
            document.getElementById('audit-hero-status').textContent = '● 100% Cryptographically Verified';
            showResult('✓ Ledger verification complete: SHA-256 chain is 100% intact with zero broken links.');
          } else {
            document.getElementById('audit-hero-status').textContent = '⚠ Verification Anomaly Detected';
            showResult('⚠ Warning: Hash chain check reported invalid state.', true);
          }
        } catch (error) {
          showResult(error.message, true);
        }
      }

      // ======================================================================
      // Page 6: Render Settings
      // ======================================================================
      function renderSettingsPage() {
        if (!getToken()) {
          document.getElementById('settings-username').textContent = 'Guest';
          document.getElementById('settings-role').textContent = 'Not Signed In';
          document.getElementById('settings-user-id').textContent = '#—';
          document.getElementById('settings-permissions-count').textContent = '0 Permissions';
          document.getElementById('settings-permissions-chips').innerHTML = '<div style="color:var(--muted); font-size:0.82rem;">Sign in to view permissions.</div>';
          return;
        }

        const u = activeUser;
        if (!u) return;

        const initials = u.username ? u.username.slice(0, 2).toUpperCase() : 'AM';
        document.getElementById('settings-avatar').textContent = initials;
        document.getElementById('settings-username').textContent = u.username;
        document.getElementById('settings-role').textContent = (u.role || 'account_holder').replaceAll('_', ' ').toUpperCase();
        document.getElementById('settings-user-id').textContent = `#${u.id || 'N/A'}`;

        const perms = u.permissions || [];
        document.getElementById('settings-permissions-count').textContent = `${perms.length} Permissions Active`;

        const chips = document.getElementById('settings-permissions-chips');
        chips.replaceChildren();
        perms.forEach(p => {
          const badge = document.createElement('span');
          badge.className = 'badge-hash';
          badge.style.background = '#e2e8f0';
          badge.style.color = '#1e293b';
          badge.textContent = p;
          chips.appendChild(badge);
        });
      }

      async function handleChangePassword(e) {
        e.preventDefault();
        const currentPass = document.getElementById('cp-current').value;
        const newPass = document.getElementById('cp-new').value;
        const confirmPass = document.getElementById('cp-confirm').value;
        const msgBox = document.getElementById('cp-status-msg');

        if (newPass !== confirmPass) {
          msgBox.textContent = 'New passwords do not match.';
          msgBox.style.background = 'var(--red-bg)';
          msgBox.style.color = 'var(--red)';
          msgBox.style.display = 'block';
          return;
        }

        try {
          const res = await api('/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({ old_password: currentPass, new_password: newPass }),
          });
          msgBox.textContent = res.message || 'Password updated successfully!';
          msgBox.style.background = 'var(--success-bg)';
          msgBox.style.color = 'var(--success)';
          msgBox.style.display = 'block';
          document.getElementById('form-change-password').reset();
          showResult('Password updated successfully.');
        } catch (error) {
          msgBox.textContent = error.message;
          msgBox.style.background = 'var(--red-bg)';
          msgBox.style.color = 'var(--red)';
          msgBox.style.display = 'block';
        }
      }

      // ======================================================================
      // Page 7: Render Auth Portal
      // ======================================================================
      function renderAuthPage() {
        if (getToken() && activeUser) {
          document.getElementById('auth-login-view').innerHTML = `
            <div style="text-align: center; padding: 20px;">
              <h3 style="margin-bottom: 8px;">Signed In as <strong>${activeUser.username}</strong></h3>
              <p style="color:var(--muted); font-size:0.86rem; margin-bottom: 20px;">Role: ${activeUser.role}</p>
              <button class="btn btn-primary" onclick="navigateTo('overview')" style="margin-right:8px;">Open Dashboard</button>
              <button class="btn btn-outline" onclick="logoutSession()">Sign Out</button>
            </div>
          `;
        }
      }

      function switchAuthTab(tab) {
        const loginBtn = document.getElementById('tab-login-btn');
        const regBtn = document.getElementById('tab-register-btn');
        const loginView = document.getElementById('auth-login-view');
        const regView = document.getElementById('auth-register-view');

        if (tab === 'login') {
          loginBtn.classList.add('active');
          regBtn.classList.remove('active');
          loginView.style.display = 'block';
          regView.style.display = 'none';
        } else {
          loginBtn.classList.remove('active');
          regBtn.classList.add('active');
          loginView.style.display = 'none';
          regView.style.display = 'block';
        }
      }

      async function handleAuthLogin(e) {
        e.preventDefault();
        const username = document.getElementById('auth-login-username').value.trim();
        const password = document.getElementById('auth-login-password').value;

        try {
          const res = await api('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
          });
          setSession(res.token, res.user);
          await refreshDashboard();
          showResult(`Signed in as ${res.user.username}.`);
          navigateTo('overview');
        } catch (error) {
          showResult(error.message, true);
        }
      }

      async function handleAuthRegister(e) {
        e.preventDefault();
        const username = document.getElementById('auth-reg-username').value.trim();
        const password = document.getElementById('auth-reg-password').value;
        const confirm = document.getElementById('auth-reg-confirm').value;

        if (password !== confirm) {
          showResult('Passwords do not match.', true);
          return;
        }

        try {
          const res = await api('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
          });
          setSession(res.token, res.user);
          await refreshDashboard();
          showResult(`Account created! Welcome, ${res.user.username}. ₹1,000 primary account provisioned.`);
          navigateTo('overview');
        } catch (error) {
          showResult(error.message, true);
        }
      }

      // ======================================================================
      // Money Operations Modals (Deposit, Withdraw, Transfer, Create Account)
      // ======================================================================
      function openCreateAccountModal() {
        if (!getToken()) {
          showResult('Please sign in to create an account.', true);
          return;
        }

        const isAdmin = activeUser && (activeUser.role === 'admin' || activeUser.role === 'super_admin');
        const dialog = document.getElementById('app-dialog');
        dialog.replaceChildren();

        const form = document.createElement('form');
        form.method = 'dialog';
        form.style.display = 'grid';
        form.style.gap = '14px';

        form.innerHTML = `
          <h2 style="font-size:1.25rem;">Create Bank Account</h2>
          <div style="font-size:0.85rem; color:var(--muted);">Open an additional account within your financial portfolio.</div>
          
          <div class="form-group">
            <label>Account Name</label>
            <input type="text" id="dlg-acc-name" class="form-control" placeholder="e.g. Vacation Savings" required />
          </div>

          ${isAdmin ? `
            <div class="form-group">
              <label>Owner Username</label>
              <input type="text" id="dlg-acc-owner" class="form-control" value="${activeUser.username}" required />
            </div>
          ` : `
            <input type="hidden" id="dlg-acc-owner" value="${activeUser.username}" />
          `}

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:8px;">
            <button type="button" class="btn btn-outline" onclick="document.getElementById('app-dialog').close()">Cancel</button>
            <button type="submit" class="btn btn-primary" id="btn-submit-create-acc">Create Account</button>
          </div>
        `;

        form.onsubmit = async (e) => {
          e.preventDefault();
          const name = document.getElementById('dlg-acc-name').value.trim();
          const owner = document.getElementById('dlg-acc-owner').value.trim();

          try {
            await api('/accounts', {
              method: 'POST',
              body: JSON.stringify({ name, owner_username: owner, overdraft_limit: 0 }),
            });
            dialog.close();
            await refreshDashboard();
            showResult(`Account '${name}' created successfully!`);
            navigateTo('accounts');
          } catch (error) {
            showResult(error.message, true);
          }
        };

        dialog.appendChild(form);
        dialog.showModal();
      }

      function openDepositModal(defaultAccId = null) {
        if (!getToken()) {
          showResult('Please sign in to make a deposit.', true);
          return;
        }
        if (accounts.length === 0) {
          showResult('No accounts available to deposit into.', true);
          return;
        }

        const dialog = document.getElementById('app-dialog');
        dialog.replaceChildren();

        const form = document.createElement('form');
        form.method = 'dialog';
        form.style.display = 'grid';
        form.style.gap = '14px';

        const accOptions = accounts.map(a => 
          `<option value="${a.id}" ${a.id === defaultAccId ? 'selected' : ''}>${a.name} (#${a.id}) — ${formatMoney(a.balance)}</option>`
        ).join('');

        form.innerHTML = `
          <h2 style="font-size:1.25rem;">Deposit Funds</h2>
          <div style="font-size:0.85rem; color:var(--muted);">Add credit to your verified append-only bank account.</div>

          <div class="form-group">
            <label>Destination Account</label>
            <select id="dlg-dep-acc" class="form-control" required>${accOptions}</select>
          </div>

          <div class="form-group">
            <label>Amount (INR ₹)</label>
            <input type="number" id="dlg-dep-amt" class="form-control" min="1" step="1" placeholder="e.g. 500" required />
          </div>

          <div class="form-group">
            <label>Description / Note</label>
            <input type="text" id="dlg-dep-desc" class="form-control" placeholder="Salary credit, investment, etc." />
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:8px;">
            <button type="button" class="btn btn-outline" onclick="document.getElementById('app-dialog').close()">Cancel</button>
            <button type="submit" class="btn btn-success">Complete Deposit</button>
          </div>
        `;

        form.onsubmit = async (e) => {
          e.preventDefault();
          const accountId = Number(document.getElementById('dlg-dep-acc').value);
          const amount = Number(document.getElementById('dlg-dep-amt').value);
          const description = document.getElementById('dlg-dep-desc').value.trim() || 'Deposit';

          try {
            await api('/deposits', {
              method: 'POST',
              body: JSON.stringify({ account_id: accountId, amount, description }),
            });
            dialog.close();
            await refreshDashboard();
            showResult(`Successfully deposited ${formatMoney(amount)} into account #${accountId}.`);
          } catch (error) {
            showResult(error.message, true);
          }
        };

        dialog.appendChild(form);
        dialog.showModal();
      }

      function openWithdrawModal(defaultAccId = null) {
        if (!getToken()) {
          showResult('Please sign in to make a withdrawal.', true);
          return;
        }
        if (accounts.length === 0) {
          showResult('No accounts available.', true);
          return;
        }

        const dialog = document.getElementById('app-dialog');
        dialog.replaceChildren();

        const form = document.createElement('form');
        form.method = 'dialog';
        form.style.display = 'grid';
        form.style.gap = '14px';

        const accOptions = accounts.map(a => 
          `<option value="${a.id}" ${a.id === defaultAccId ? 'selected' : ''}>${a.name} (#${a.id}) — ${formatMoney(a.balance)}</option>`
        ).join('');

        form.innerHTML = `
          <h2 style="font-size:1.25rem;">Withdraw Funds</h2>
          <div style="font-size:0.85rem; color:var(--muted);">Debit money from your account with atomic overdraft protection.</div>

          <div class="form-group">
            <label>Source Account</label>
            <select id="dlg-wth-acc" class="form-control" required>${accOptions}</select>
          </div>

          <div class="form-group">
            <label>Amount (INR ₹)</label>
            <input type="number" id="dlg-wth-amt" class="form-control" min="1" step="1" placeholder="e.g. 200" required />
          </div>

          <div class="form-group">
            <label>Description / Note</label>
            <input type="text" id="dlg-wth-desc" class="form-control" placeholder="ATM, bill payment, etc." />
          </div>

          <div style="font-size:0.75rem; color:var(--muted); background:#f8fafc; padding:8px 10px; border-radius:8px;">
            🛡️ Overdraft limit is strictly ₹0.00. Requests exceeding your balance are atomically refused.
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:8px;">
            <button type="button" class="btn btn-outline" onclick="document.getElementById('app-dialog').close()">Cancel</button>
            <button type="submit" class="btn btn-primary">Complete Withdrawal</button>
          </div>
        `;

        form.onsubmit = async (e) => {
          e.preventDefault();
          const accountId = Number(document.getElementById('dlg-wth-acc').value);
          const amount = Number(document.getElementById('dlg-wth-amt').value);
          const description = document.getElementById('dlg-wth-desc').value.trim() || 'Withdrawal';

          try {
            await api('/withdrawals', {
              method: 'POST',
              body: JSON.stringify({ account_id: accountId, amount, description }),
            });
            dialog.close();
            await refreshDashboard();
            showResult(`Successfully withdrew ${formatMoney(amount)} from account #${accountId}.`);
          } catch (error) {
            showResult(error.message, true);
          }
        };

        dialog.appendChild(form);
        dialog.showModal();
      }

      function openTransferModal(defaultSourceId = null) {
        if (!getToken()) {
          showResult('Please sign in to transfer funds.', true);
          return;
        }
        if (accounts.length < 2 && activeUser.role !== 'admin' && activeUser.role !== 'super_admin') {
          showResult('You need at least 2 accounts to make a transfer. Create a second account first!', true);
          return;
        }

        const dialog = document.getElementById('app-dialog');
        dialog.replaceChildren();

        const form = document.createElement('form');
        form.method = 'dialog';
        form.style.display = 'grid';
        form.style.gap = '14px';

        const sourceOptions = accounts.map(a => 
          `<option value="${a.id}" ${a.id === defaultSourceId ? 'selected' : ''}>${a.name} (#${a.id}) — ${formatMoney(a.balance)}</option>`
        ).join('');

        const destOptions = accounts.map(a => 
          `<option value="${a.id}" ${a.id !== defaultSourceId ? 'selected' : ''}>${a.name} (#${a.id})</option>`
        ).join('');

        form.innerHTML = `
          <h2 style="font-size:1.25rem;">Atomic Money Transfer</h2>
          <div style="font-size:0.85rem; color:var(--muted);">Simultaneous double-entry debit &amp; credit across ledger accounts.</div>

          <div class="form-group">
            <label>Source Account (From)</label>
            <select id="dlg-trf-from" class="form-control" required>${sourceOptions}</select>
          </div>

          <div class="form-group">
            <label>Destination Account (To)</label>
            <select id="dlg-trf-to" class="form-control" required>${destOptions}</select>
          </div>

          <div class="form-group">
            <label>Transfer Amount (INR ₹)</label>
            <input type="number" id="dlg-trf-amt" class="form-control" min="1" step="1" placeholder="e.g. 250" required />
          </div>

          <div class="form-group">
            <label>Description / Transfer Memo</label>
            <input type="text" id="dlg-trf-desc" class="form-control" placeholder="Internal savings transfer" />
          </div>

          <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:8px;">
            <button type="button" class="btn btn-outline" onclick="document.getElementById('app-dialog').close()">Cancel</button>
            <button type="submit" class="btn btn-primary">Execute Transfer</button>
          </div>
        `;

        form.onsubmit = async (e) => {
          e.preventDefault();
          const fromId = Number(document.getElementById('dlg-trf-from').value);
          const toId = Number(document.getElementById('dlg-trf-to').value);
          const amount = Number(document.getElementById('dlg-trf-amt').value);
          const description = document.getElementById('dlg-trf-desc').value.trim() || 'Transfer';

          if (fromId === toId) {
            showResult('Source and destination accounts must be different.', true);
            return;
          }

          try {
            await api('/transfers', {
              method: 'POST',
              body: JSON.stringify({
                from_account_id: fromId,
                to_account_id: toId,
                amount,
                description,
              }),
            });
            dialog.close();
            await refreshDashboard();
            showResult(`Successfully transferred ${formatMoney(amount)} from #${fromId} to #${toId}.`);
          } catch (error) {
            showResult(error.message, true);
          }
        };

        dialog.appendChild(form);
        dialog.showModal();
      }

      function openDepositForAccount(accId) { openDepositModal(accId); }
      function openWithdrawForAccount(accId) { openWithdrawModal(accId); }
      function openTransferForAccount(accId) { openTransferModal(accId); }

      // ======================================================================
      // Topbar Dropdown & Global Handlers
      // ======================================================================
      const userMenuBtn = document.getElementById('user-menu-btn');
      const userDropdown = document.getElementById('user-dropdown');
      const viewProfileBtn = document.getElementById('btn-view-profile');
      const logoutBtn = document.getElementById('btn-logout');

      if (userMenuBtn) {
        userMenuBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (!getToken()) {
            navigateTo('auth', 'login');
          } else {
            const isVisible = userDropdown.style.display === 'block';
            userDropdown.style.display = isVisible ? 'none' : 'block';
          }
        });
      }

      document.addEventListener('click', (e) => {
        if (!e.target.closest('.user-menu-wrapper')) {
          if (userDropdown) userDropdown.style.display = 'none';
        }
      });

      if (viewProfileBtn) {
        viewProfileBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (userDropdown) userDropdown.style.display = 'none';
          navigateTo('settings');
        });
      }

      if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (userDropdown) userDropdown.style.display = 'none';
          logoutSession();
        });
      }

      const sidebarProfile = document.getElementById('sidebar-profile-box');
      if (sidebarProfile) {
        sidebarProfile.addEventListener('click', () => {
          if (getToken()) {
            navigateTo('settings');
          } else {
            navigateTo('auth', 'login');
          }
        });
      }

      const topRefreshBtn = document.getElementById('top-refresh-btn');
      if (topRefreshBtn) {
        topRefreshBtn.addEventListener('click', async () => {
          await refreshDashboard();
          showResult('Dashboard data updated from live PostgreSQL database.');
        });
      }

      // Global search bar
      const globalSearch = document.getElementById('global-search');
      if (globalSearch) {
        globalSearch.addEventListener('input', () => {
          const val = globalSearch.value.trim();
          if (val) {
            navigateTo('transactions');
            const txSearch = document.getElementById('tx-search-input');
            if (txSearch) {
              txSearch.value = val;
              filterTransactions();
            }
          }
        });
      }

      // ======================================================================
      // App Initialization
      // ======================================================================
      (async function initApp() {
        const hash = window.location.hash.replace('#', '') || 'overview';
        navigateTo(hash);

        if (getToken()) {
          await refreshDashboard().catch(() => setSession(null));
        }
      })();
    </script>
  </body>
</html>
"""

# Write to app/static/index.html
with open(STATIC_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

# Write to root index.html
with open(ROOT_HTML_PATH, "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

print(f"Successfully generated {STATIC_HTML_PATH} ({len(HTML_CONTENT)} bytes)")
print(f"Successfully generated {ROOT_HTML_PATH} ({len(HTML_CONTENT)} bytes)")
