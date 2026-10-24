"""Скрипт генерации векторных SVG-макетов экранов веб-сервиса учёта дедлайнов для импорта в Figma."""

import os

FONT = "font-family=\"'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif\""

def get_svg_wrapper(width, height, title, content):
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg" {FONT}>
  <defs>
    <filter id="card-shadow" x="-4" y="-2" width="108%" height="110%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#0F172A" flood-opacity="0.05" />
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#0F172A" flood-opacity="0.04" />
    </filter>
    <filter id="modal-shadow" x="-20" y="-10" width="120%" height="120%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="20" stdDeviation="25" flood-color="#0F172A" flood-opacity="0.25" />
    </filter>
    <linearGradient id="hero-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4F46E5" />
      <stop offset="100%" stop-color="#7C3AED" />
    </linearGradient>
    <linearGradient id="accent-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#6366F1" />
      <stop offset="100%" stop-color="#8B5CF6" />
    </linearGradient>
  </defs>
  
  <rect width="{width}" height="{height}" fill="#F8FAFC" />
  <!-- Title Metadata for Figma -->
  <desc>{title}</desc>
{content}
</svg>"""

def render_sidebar(active_item="dashboard", is_starosta=False):
    items = [
        ("dashboard", "⚡", "Главный дашборд", None),
        ("calendar", "📅", "Календарь дедлайнов", "N(d)≥3"),
        ("subjects", "📚", "Дисциплины", None),
        ("tasks", "📝", "Задания и варианты", "2"),
        ("announcements", "📢", "Объявления группы", "1"),
        ("analytics", "📊", "Матрица успеваемости", "Староста" if is_starosta else None),
        ("profile", "👤", "Личный кабинет", None),
    ]
    
    sidebar = f"""
  <g id="Sidebar" width="260">
    <rect width="260" height="900" fill="#0F172A" />
    
    <!-- Logo & Brand -->
    <g id="Logo" transform="translate(24, 28)">
      <rect width="36" height="36" rx="10" fill="url(#accent-grad)" />
      <text x="18" y="24" fill="#FFFFFF" font-size="18" font-weight="bold" text-anchor="middle">⏱</text>
      <text x="48" y="24" fill="#FFFFFF" font-size="18" font-weight="700">StudyPulse</text>
      <text x="48" y="38" fill="#94A3B8" font-size="11" font-weight="500">УЧЁТ ДЕДЛАЙНОВ • 921701</text>
    </g>
    
    <!-- Nav Items -->
    <g id="Navigation" transform="translate(16, 96)">
"""
    y_offset = 0
    for key, icon, label, badge in items:
        is_active = (key == active_item)
        bg_fill = "#1E293B" if is_active else "transparent"
        text_fill = "#FFFFFF" if is_active else "#94A3B8"
        font_weight = "600" if is_active else "500"
        
        sidebar += f"""      <g id="NavItem-{key}" transform="translate(0, {y_offset})">
        <rect width="228" height="44" rx="8" fill="{bg_fill}" />
        {"<rect x='0' y='6' width='4' height='32' rx='2' fill='#6366F1' />" if is_active else ""}
        <text x="16" y="28" font-size="16">{icon}</text>
        <text x="44" y="28" fill="{text_fill}" font-size="14" font-weight="{font_weight}">{label}</text>
"""
        if badge:
            badge_bg = "#EF4444" if badge in ["2", "1"] else ("#6366F1" if "Староста" in badge else "#8B5CF6")
            sidebar += f"""        <rect x="175" y="12" width="42" height="20" rx="10" fill="{badge_bg}" />
        <text x="196" y="26" fill="#FFFFFF" font-size="11" font-weight="600" text-anchor="middle">{badge}</text>
"""
        sidebar += f"""      </g>\n"""
        y_offset += 52

    sidebar += f"""    </g>
    
    <!-- System Status & Belarus Law -->
    <g id="LawCompliance" transform="translate(20, 720)">
      <rect width="220" height="58" rx="8" fill="#1E293B" />
      <text x="14" y="24" fill="#10B981" font-size="12">🛡 Закон РБ № 99-З</text>
      <text x="14" y="44" fill="#64748B" font-size="11">Персональные данные защищены</text>
    </g>
    
    <!-- User Card -->
    <g id="CurrentUser" transform="translate(20, 800)">
      <rect width="220" height="72" rx="12" fill="#1E293B" />
      <circle cx="36" cy="36" r="20" fill="#6366F1" />
      <text x="36" y="42" fill="#FFFFFF" font-size="14" font-weight="bold" text-anchor="middle">ДК</text>
      <text x="68" y="30" fill="#FFFFFF" font-size="13" font-weight="600">Данила Кабердин</text>
      <text x="68" y="46" fill="#10B981" font-size="11" font-weight="500">● Студент (Подгруппа 1)</text>
      <text x="194" y="40" fill="#64748B" font-size="16">⚙</text>
    </g>
  </g>
"""
    return sidebar

def render_header(title, subtitle, quick_action_text="+ Сдать работу"):
    return f"""
  <g id="Header" transform="translate(260, 0)">
    <rect width="1180" height="72" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1" />
    
    <text x="32" y="32" fill="#0F172A" font-size="20" font-weight="700">{title}</text>
    <text x="32" y="52" fill="#64748B" font-size="12">{subtitle}</text>
    
    <!-- Search Bar -->
    <g id="SearchBar" transform="translate(620, 16)">
      <rect width="240" height="40" rx="8" fill="#F1F5F9" stroke="#E2E8F0" />
      <text x="14" y="25" fill="#94A3B8" font-size="14">🔍</text>
      <text x="38" y="25" fill="#94A3B8" font-size="13">Поиск дисциплины или задания...</text>
    </g>
    
    <!-- Notifications Bell -->
    <g id="Bell" transform="translate(880, 18)">
      <rect width="36" height="36" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
      <text x="11" y="24" font-size="16">🔔</text>
      <circle cx="27" cy="11" r="5" fill="#EF4444" stroke="#FFFFFF" stroke-width="1.5" />
    </g>
    
    <!-- Quick Action Button -->
    <g id="QuickActionButton" transform="translate(936, 16)">
      <rect width="180" height="40" rx="8" fill="#4F46E5" />
      <text x="90" y="25" fill="#FFFFFF" font-size="13" font-weight="600" text-anchor="middle">{quick_action_text}</text>
    </g>
  </g>
"""

# Screen 1: Dashboard
def create_dashboard_svg():
    sidebar = render_sidebar("dashboard")
    header = render_header("Панель управления дедлайнами", "Осенний семестр 2026/2027 • Учебная группа 921701")
    
    content = f"""{sidebar}
{header}
  <g id="DashboardContent" transform="translate(292, 96)">
    <!-- Hero Banner -->
    <g id="HeroBanner" filter="url(#card-shadow)">
      <rect width="1116" height="106" rx="16" fill="url(#hero-grad)" />
      <text x="32" y="42" fill="#FFFFFF" font-size="22" font-weight="700">Привет, Данила! 👋 У вас 3 активных дедлайна на этой неделе</text>
      <text x="32" y="68" fill="#E0E7FF" font-size="14">Ближайший: Операционные системы (ЛР №3) • Осталось 14 часов • Вариант 7 (закреплён)</text>
      
      <rect x="890" y="32" width="194" height="42" rx="8" fill="#FFFFFF" />
      <text x="987" y="58" fill="#4F46E5" font-size="13" font-weight="700" text-anchor="middle">Перейти к сдаче ЛР №3 →</text>
    </g>
    
    <!-- Metrics Cards Row -->
    <g id="MetricsRow" transform="translate(0, 126)">
      <!-- Card 1 -->
      <g id="Metric-1" filter="url(#card-shadow)">
        <rect width="264" height="96" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        <text x="20" y="32" fill="#64748B" font-size="12" font-weight="600">🔥 СРОЧНЫЕ ДЕДЛАЙНЫ (&lt; 48Ч)</text>
        <text x="20" y="68" fill="#EF4444" font-size="28" font-weight="800">2 работы</text>
        <rect x="180" y="20" width="64" height="24" rx="6" fill="#FEE2E2" />
        <text x="212" y="36" fill="#B91C1C" font-size="11" font-weight="700" text-anchor="middle">Внимание</text>
      </g>
      
      <!-- Card 2 -->
      <g id="Metric-2" transform="translate(284, 0)" filter="url(#card-shadow)">
        <rect width="264" height="96" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        <text x="20" y="32" fill="#64748B" font-size="12" font-weight="600">⏳ НА ПРОВЕРКЕ У СТАРОСТЫ</text>
        <text x="20" y="68" fill="#3B82F6" font-size="28" font-weight="800">1 работа</text>
        <rect x="190" y="20" width="54" height="24" rx="6" fill="#DBEAFE" />
        <text x="217" y="36" fill="#1D4ED8" font-size="11" font-weight="700" text-anchor="middle">Ожидает</text>
      </g>
      
      <!-- Card 3 -->
      <g id="Metric-3" transform="translate(568, 0)" filter="url(#card-shadow)">
        <rect width="264" height="96" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        <text x="20" y="32" fill="#64748B" font-size="12" font-weight="600">✅ УСПЕВАЕМОСТЬ (ЗАЧТЕНО)</text>
        <text x="20" y="68" fill="#10B981" font-size="28" font-weight="800">14 из 22</text>
        <text x="170" y="68" fill="#64748B" font-size="16" font-weight="600">(64%)</text>
      </g>
      
      <!-- Card 4 -->
      <g id="Metric-4" transform="translate(852, 0)" filter="url(#card-shadow)">
        <rect width="264" height="96" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        <text x="20" y="32" fill="#64748B" font-size="12" font-weight="600">📅 ДЕНЬ ПИКОВОЙ НАГРУЗКИ</text>
        <text x="20" y="68" fill="#8B5CF6" font-size="24" font-weight="800">Ср, 28 окт</text>
        <rect x="175" y="20" width="68" height="24" rx="6" fill="#F3E8FF" />
        <text x="209" y="36" fill="#7E22CE" font-size="11" font-weight="700" text-anchor="middle">N(d)=3</text>
      </g>
    </g>
    
    <!-- Main Two-Column Section -->
    <g id="MainSection" transform="translate(0, 244)">
      <!-- Left Column: Upcoming Tasks List (Width 700) -->
      <g id="UpcomingTasks" filter="url(#card-shadow)">
        <rect width="700" height="490" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        <text x="24" y="36" fill="#0F172A" font-size="17" font-weight="700">Ближайшие дедлайны (Приоритет: Персональный ≻ Подгруппа ≻ Общий)</text>
        
        <!-- Task Item 1: ОС ЛР3 (Urgent) -->
        <g id="TaskItem-1" transform="translate(24, 60)">
          <rect width="652" height="116" rx="10" fill="#FEF2F2" stroke="#FCA5A5" />
          <rect x="16" y="16" width="94" height="22" rx="4" fill="#EF4444" />
          <text x="63" y="32" fill="#FFFFFF" font-size="11" font-weight="700" text-anchor="middle">14 ЧАСОВ</text>
          
          <rect x="118" y="16" width="136" height="22" rx="4" fill="#FEE2E2" />
          <text x="186" y="32" fill="#991B1B" font-size="11" font-weight="600" text-anchor="middle">⭐ Персональный дедлайн</text>
          
          <text x="16" y="64" fill="#0F172A" font-size="16" font-weight="700">Операционные системы • Лабораторная работа №3</text>
          <text x="16" y="86" fill="#64748B" font-size="13">Тема: «Синхронизация потоков POSIX mutex» • Назначен Вариант: 7 • Преп. Сидоров В.П.</text>
          
          <rect x="16" y="96" width="280" height="6" rx="3" fill="#E2E8F0" />
          <rect x="16" y="96" width="190" height="6" rx="3" fill="#EF4444" />
          
          <rect x="520" y="44" width="116" height="36" rx="6" fill="#EF4444" />
          <text x="578" y="67" fill="#FFFFFF" font-size="13" font-weight="600" text-anchor="middle">Сдать отчёт</text>
        </g>
        
        <!-- Task Item 2: СПО Практика 4 -->
        <g id="TaskItem-2" transform="translate(24, 192)">
          <rect width="652" height="116" rx="10" fill="#FFFFFF" stroke="#E2E8F0" />
          <rect x="16" y="16" width="76" height="22" rx="4" fill="#F59E0B" />
          <text x="54" y="32" fill="#FFFFFF" font-size="11" font-weight="700" text-anchor="middle">2 ДНЯ</text>
          
          <rect x="100" y="16" width="120" height="22" rx="4" fill="#FEF3C7" />
          <text x="160" y="32" fill="#92400E" font-size="11" font-weight="600" text-anchor="middle">👥 Подгруппа №1</text>
          
          <text x="16" y="64" fill="#0F172A" font-size="16" font-weight="700">Системное программное обеспечение • Практика №4</text>
          <text x="16" y="86" fill="#64748B" font-size="13">Дедлайн: 26 октября, 23:59 • Статус: «В процессе» • Вариант 1</text>
          
          <rect x="520" y="44" width="116" height="36" rx="6" fill="#F1F5F9" stroke="#CBD5E1" />
          <text x="578" y="67" fill="#334155" font-size="13" font-weight="600" text-anchor="middle">Открыть карточку</text>
        </g>
        
        <!-- Task Item 3: Базы данных КР -->
        <g id="TaskItem-3" transform="translate(24, 324)">
          <rect width="652" height="116" rx="10" fill="#FFFFFF" stroke="#E2E8F0" />
          <rect x="16" y="16" width="76" height="22" rx="4" fill="#10B981" />
          <text x="54" y="32" fill="#FFFFFF" font-size="11" font-weight="700" text-anchor="middle">5 ДНЕЙ</text>
          
          <rect x="100" y="16" width="110" height="22" rx="4" fill="#E0E7FF" />
          <text x="155" y="32" fill="#3730A3" font-size="11" font-weight="600" text-anchor="middle">🌐 Общий дедлайн</text>
          
          <text x="16" y="64" fill="#0F172A" font-size="16" font-weight="700">Базы данных • Курсовая работа (Этап 1: Схема ERD)</text>
          <text x="16" y="86" fill="#64748B" font-size="13">Дедлайн: 29 октября, 18:00 • Статус: «Сдано на проверку» (Ожидает старосту)</text>
          
          <rect x="500" y="44" width="136" height="36" rx="6" fill="#EFF6FF" stroke="#BFDBFE" />
          <text x="568" y="67" fill="#1D4ED8" font-size="12" font-weight="600" text-anchor="middle">⏳ На верификации</text>
        </g>
      </g>
      
      <!-- Right Column: Announcements & Fast Tools (Width 390) -->
      <g id="RightWidgets" transform="translate(726, 0)">
        <!-- Announcements Widget -->
        <g id="AnnouncementsCard" filter="url(#card-shadow)">
          <rect width="390" height="290" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
          <text x="24" y="36" fill="#0F172A" font-size="16" font-weight="700">📢 Объявления старосты</text>
          
          <!-- Post 1 -->
          <g id="Post-1" transform="translate(20, 56)">
            <rect width="350" height="96" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
            <text x="16" y="24" fill="#6366F1" font-size="11" font-weight="700">СТАРОСТА • ВЛАД КАХНОВИЧ • 23.10 14:15</text>
            <text x="16" y="46" fill="#0F172A" font-size="13" font-weight="700">Перенос дедлайна по Базам данных!</text>
            <text x="16" y="66" fill="#475569" font-size="12">Преподаватель перенёс срок сдачи первого этапа курсовой на 29 октября.</text>
          </g>
          
          <!-- Post 2 -->
          <g id="Post-2" transform="translate(20, 164)">
            <rect width="350" height="96" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
            <text x="16" y="24" fill="#64748B" font-size="11" font-weight="700">ОБЪЯВЛЕНИЕ • 21.10 10:00</text>
            <text x="16" y="46" fill="#0F172A" font-size="13" font-weight="700">Защита лабораторных работ №2 по СПО</text>
            <text x="16" y="66" fill="#475569" font-size="12">В субботу защита пройдёт очно в ауд. 312. Приносите распечатанные отчёты.</text>
          </g>
        </g>
        
        <!-- Starosta Performance Badge & Fast Actions -->
        <g id="FastActionsCard" transform="translate(0, 310)" filter="url(#card-shadow)">
          <rect width="390" height="180" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
          <text x="24" y="36" fill="#0F172A" font-size="16" font-weight="700">⚡ Быстрый переход</text>
          
          <rect x="24" y="56" width="342" height="42" rx="8" fill="#F1F5F9" />
          <text x="44" y="82" font-size="16">📅</text>
          <text x="74" y="82" fill="#1E293B" font-size="13" font-weight="600">Открыть интерактивный календарь</text>
          <text x="340" y="82" fill="#94A3B8" font-size="14">→</text>
          
          <rect x="24" y="110" width="342" height="42" rx="8" fill="#EEF2FF" stroke="#C7D2FE" />
          <text x="44" y="136" font-size="16">📊</text>
          <text x="74" y="136" fill="#4338CA" font-size="13" font-weight="600">Сводная матрица успеваемости группы</text>
          <text x="340" y="136" fill="#6366F1" font-size="14">→</text>
        </g>
      </g>
    </g>
  </g>
"""
    return get_svg_wrapper(1440, 900, "01_Главный_Дашборд_Студента", content)

# Screen 2: Interactive Calendar with Peak Workload N(d) >= 3
def create_calendar_svg():
    sidebar = render_sidebar("calendar")
    header = render_header("Интерактивный календарь дедлайнов", "Октябрь 2026 • Расчёт пиковой нагрузки N(d) ≥ 3 по п. 4.3 ТЗ", "+ Новое событие")
    
    content = f"""{sidebar}
{header}
  <g id="CalendarContent" transform="translate(292, 96)">
    <!-- Calendar Controls Bar -->
    <g id="CalendarControls" filter="url(#card-shadow)">
      <rect width="1116" height="64" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
      
      <text x="24" y="38" fill="#0F172A" font-size="18" font-weight="700">Октябрь 2026 г.</text>
      
      <!-- Prev / Next / Today Buttons -->
      <g transform="translate(180, 16)">
        <rect width="32" height="32" rx="6" fill="#F1F5F9" />
        <text x="16" y="21" fill="#334155" font-size="14" text-anchor="middle">‹</text>
        <rect x="38" y="0" width="32" height="32" rx="6" fill="#F1F5F9" />
        <text x="54" y="21" fill="#334155" font-size="14" text-anchor="middle">›</text>
        <rect x="76" y="0" width="70" height="32" rx="6" fill="#F1F5F9" />
        <text x="111" y="20" fill="#334155" font-size="12" font-weight="600" text-anchor="middle">Сегодня</text>
      </g>
      
      <!-- Legend for Priorities & Peak Load -->
      <g transform="translate(520, 22)">
        <circle cx="8" cy="10" r="5" fill="#EF4444" />
        <text x="20" y="14" fill="#475569" font-size="12">Персональный [П]</text>
        
        <circle cx="150" cy="10" r="5" fill="#F59E0B" />
        <text x="162" y="14" fill="#475569" font-size="12">Подгруппа [ПГ]</text>
        
        <circle cx="280" cy="10" r="5" fill="#3B82F6" />
        <text x="292" y="14" fill="#475569" font-size="12">Общий [ОБЩ]</text>
        
        <rect x="400" y="0" width="170" height="22" rx="4" fill="#FEE2E2" stroke="#FCA5A5" />
        <text x="485" y="15" fill="#991B1B" font-size="11" font-weight="700" text-anchor="middle">🔥 Пик нагрузки N(d)≥3</text>
      </g>
    </g>
    
    <!-- Calendar Grid (Width 760) & Selected Day Drawer (Width 336) -->
    <g id="CalendarBody" transform="translate(0, 80)">
      <!-- Main Month Grid Card -->
      <g id="MonthGrid" filter="url(#card-shadow)">
        <rect width="760" height="690" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        
        <!-- Day Names -->
"""
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i, d in enumerate(days):
        col_x = 20 + i * 102
        content += f"""        <text x="{col_x + 51}" y="32" fill="#64748B" font-size="13" font-weight="600" text-anchor="middle">{d}</text>\n"""
    
    content += """        <line x1="20" y1="46" x2="740" y2="46" stroke="#E2E8F0" stroke-width="1" />\n"""
    
    # 5 Weeks Grid
    # Highlighting Oct 28 (Wednesday) as Peak Workload Day N(d) = 3!
    for week in range(5):
        y_pos = 56 + week * 124
        for day_col in range(7):
            x_pos = 20 + day_col * 102
            day_num = week * 7 + day_col - 3 # arbitrary month starting Thurs
            if day_num < 1 or day_num > 31:
                # Dimmed cell
                content += f"""        <rect x="{x_pos}" y="{y_pos}" width="100" height="118" rx="6" fill="#F8FAFC" />\n"""
            elif day_num == 28:
                # PEAK WORKLOAD DAY N(d) >= 3 (High Load Day Oct 28)
                content += f"""        <!-- Day 28: High Peak Load N(d) = 3 -->
        <rect x="{x_pos}" y="{y_pos}" width="100" height="118" rx="6" fill="#FEF2F2" stroke="#EF4444" stroke-width="2" />
        <text x="{x_pos + 8}" y="{y_pos + 18}" fill="#991B1B" font-size="14" font-weight="800">28</text>
        <rect x="{x_pos + 30}" y="{y_pos + 6}" width="64" height="16" rx="4" fill="#EF4444" />
        <text x="{x_pos + 62}" y="{y_pos + 18}" fill="#FFFFFF" font-size="9" font-weight="700" text-anchor="middle">ПИК: 3 ДЕДЛ.</text>
        
        <!-- 3 Deadlines on Day 28 -->
        <rect x="{x_pos + 4}" y="{y_pos + 26}" width="92" height="26" rx="4" fill="#FEE2E2" />
        <text x="{x_pos + 8}" y="{y_pos + 42}" fill="#991B1B" font-size="9" font-weight="700">ОС • ЛР №3 [П]</text>
        
        <rect x="{x_pos + 4}" y="{y_pos + 56}" width="92" height="26" rx="4" fill="#FEF3C7" />
        <text x="{x_pos + 8}" y="{y_pos + 72}" fill="#92400E" font-size="9" font-weight="700">СПО • ПР №4 [ПГ1]</text>
        
        <rect x="{x_pos + 4}" y="{y_pos + 86}" width="92" height="26" rx="4" fill="#DBEAFE" />
        <text x="{x_pos + 8}" y="{y_pos + 102}" fill="#1E40AF" font-size="9" font-weight="700">БД • Эскиз [ОБЩ]</text>
"""
            elif day_num == 24:
                # Today (Oct 24)
                content += f"""        <rect x="{x_pos}" y="{y_pos}" width="100" height="118" rx="6" fill="#EFF6FF" stroke="#3B82F6" stroke-width="2" />
        <circle cx="{x_pos + 14}" cy="{y_pos + 14}" r="10" fill="#3B82F6" />
        <text x="{x_pos + 14}" y="{y_pos + 18}" fill="#FFFFFF" font-size="11" font-weight="700" text-anchor="middle">24</text>
        <text x="{x_pos + 32}" y="{y_pos + 18}" fill="#1E40AF" font-size="10" font-weight="600">Сегодня</text>
"""
            elif day_num in [12, 19, 31]:
                # Days with single deadlines
                content += f"""        <rect x="{x_pos}" y="{y_pos}" width="100" height="118" rx="6" fill="#FFFFFF" stroke="#E2E8F0" />
        <text x="{x_pos + 8}" y="{y_pos + 18}" fill="#1E293B" font-size="13" font-weight="600">{day_num}</text>
        <rect x="{x_pos + 4}" y="{y_pos + 30}" width="92" height="24" rx="4" fill="#E0E7FF" />
        <text x="{x_pos + 8}" y="{y_pos + 46}" fill="#3730A3" font-size="9" font-weight="600">Сети • Тест 2</text>
"""
            else:
                content += f"""        <rect x="{x_pos}" y="{y_pos}" width="100" height="118" rx="6" fill="#FFFFFF" stroke="#E2E8F0" />
        <text x="{x_pos + 8}" y="{y_pos + 18}" fill="#64748B" font-size="13">{day_num}</text>\n"""

    content += f"""      </g>
      
      <!-- Right Side Drawer: Selected Day Details (Wednesday Oct 28) -->
      <g id="SelectedDayPanel" transform="translate(780, 0)" filter="url(#card-shadow)">
        <rect width="336" height="690" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        
        <rect x="20" y="20" width="296" height="74" rx="10" fill="#FEF2F2" stroke="#FCA5A5" />
        <text x="36" y="44" fill="#991B1B" font-size="15" font-weight="700">🔥 Среда, 28 октября 2026</text>
        <text x="36" y="66" fill="#B91C1C" font-size="12">Индикатор высокой нагрузки: N(d) = 3 ≥ 3</text>
        <text x="36" y="80" fill="#7F1D1D" font-size="11">Рекомендуется начать выполнение заранее!</text>
        
        <text x="20" y="124" fill="#0F172A" font-size="14" font-weight="700">Сроки сдачи в этот день:</text>
        
        <!-- Item 1 -->
        <g id="SideItem-1" transform="translate(20, 140)">
          <rect width="296" height="96" rx="8" fill="#F8FAFC" stroke="#EF4444" stroke-width="1.5" />
          <text x="14" y="24" fill="#DC2626" font-size="11" font-weight="700">⭐ ПЕРСОНАЛЬНЫЙ ДЕДЛАЙН • 23:59</text>
          <text x="14" y="46" fill="#0F172A" font-size="13" font-weight="700">ОС • Лабораторная работа №3</text>
          <text x="14" y="66" fill="#64748B" font-size="11">Вариант: 7 • Преп. Сидоров В.П.</text>
          <rect x="14" y="74" width="76" height="16" rx="4" fill="#FEE2E2" />
          <text x="52" y="86" fill="#991B1B" font-size="10" font-weight="700" text-anchor="middle">В процессе</text>
        </g>
        
        <!-- Item 2 -->
        <g id="SideItem-2" transform="translate(20, 248)">
          <rect width="296" height="96" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
          <text x="14" y="24" fill="#D97706" font-size="11" font-weight="700">👥 ПОДГРУППА №1 • 18:00</text>
          <text x="14" y="46" fill="#0F172A" font-size="13" font-weight="700">СПО • Практика №4</text>
          <text x="14" y="66" fill="#64748B" font-size="11">Вариант: 1 • Преп. Ковалёв А.Н.</text>
          <rect x="14" y="74" width="76" height="16" rx="4" fill="#FEF3C7" />
          <text x="52" y="86" fill="#92400E" font-size="10" font-weight="700" text-anchor="middle">Не начато</text>
        </g>
        
        <!-- Item 3 -->
        <g id="SideItem-3" transform="translate(20, 356)">
          <rect width="296" height="96" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
          <text x="14" y="24" fill="#2563EB" font-size="11" font-weight="700">🌐 ОБЩИЙ ДЕДЛАЙН • 20:00</text>
          <text x="14" y="46" fill="#0F172A" font-size="13" font-weight="700">Базы данных • Эскиз ERD</text>
          <text x="14" y="66" fill="#64748B" font-size="11">Все студенты • Преп. Клебан А.С.</text>
          <rect x="14" y="74" width="100" height="16" rx="4" fill="#DBEAFE" />
          <text x="64" y="86" fill="#1E40AF" font-size="10" font-weight="700" text-anchor="middle">Сдано на проверку</text>
        </g>
        
        <!-- Advice Box -->
        <g transform="translate(20, 470)">
          <rect width="296" height="90" rx="8" fill="#F0FDF4" stroke="#86EFAC" />
          <text x="14" y="26" fill="#15803D" font-size="12" font-weight="700">💡 Совет старосты:</text>
          <text x="14" y="48" fill="#166534" font-size="11">Сдайте практику по СПО заранее во вторник,</text>
          <text x="14" y="66" fill="#166534" font-size="11">чтобы разгрузить вечер среды.</text>
        </g>
      </g>
    </g>
  </g>
"""
    return get_svg_wrapper(1440, 900, "02_Календарь_Пиковая_Нагрузка", content)

# Screen 3: Task Details Screen (Option Lock, Secure Upload, Priority)
def create_task_details_svg():
    sidebar = render_sidebar("tasks")
    header = render_header("Детали задания • ОС (ЛР №3)", "Хлебные крошки: Дисциплины › Операционные системы › Лабораторная работа №3", "⬅ К списку заданий")
    
    content = f"""{sidebar}
{header}
  <g id="TaskDetailsContent" transform="translate(292, 96)">
    <!-- Top Task Header Card -->
    <g id="TaskBanner" filter="url(#card-shadow)">
      <rect width="1116" height="140" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
      
      <rect x="24" y="20" width="120" height="24" rx="4" fill="#EEF2FF" />
      <text x="84" y="36" fill="#4F46E5" font-size="11" font-weight="700" text-anchor="middle">ДИСЦИПЛИНА: ОС</text>
      
      <rect x="154" y="20" width="160" height="24" rx="4" fill="#FEE2E2" />
      <text x="234" y="36" fill="#B91C1C" font-size="11" font-weight="700" text-anchor="middle">⭐ Персональный дедлайн</text>
      
      <text x="24" y="78" fill="#0F172A" font-size="22" font-weight="800">Лабораторная работа №3: Синхронизация потоков POSIX (Mutex &amp; Semaphores)</text>
      <text x="24" y="104" fill="#64748B" font-size="13">Преподаватель: Сидоров Виктор Павлович • Срок сдачи: 28 октября 2026, 23:59 (Осталось 14 часов)</text>
      <text x="24" y="122" fill="#10B981" font-size="12" font-weight="600">✓ Персональная отсрочка на 2 дня согласована старостой группы</text>
      
      <!-- Variant Locked Card -->
      <g transform="translate(870, 24)">
        <rect width="220" height="92" rx="10" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" />
        <text x="20" y="30" fill="#64748B" font-size="11" font-weight="700">ЗАКРЕПЛЁННЫЙ ВАРИАНТ</text>
        <text x="20" y="64" fill="#4F46E5" font-size="28" font-weight="900">Вариант 7</text>
        <text x="20" y="82" fill="#10B981" font-size="11" font-weight="600">🔒 Не сбивается (ID: 921701-07)</text>
      </g>
    </g>
    
    <!-- Split Columns: Task Info (Left 680) & Submission Form (Right 412) -->
    <g id="TaskColumns" transform="translate(0, 160)">
      <!-- Left: Description and Materials -->
      <g id="TaskDescriptionCard" filter="url(#card-shadow)">
        <rect width="680" height="574" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        
        <text x="24" y="36" fill="#0F172A" font-size="16" font-weight="700">📋 Описание задания и требования</text>
        <text x="24" y="66" fill="#334155" font-size="13">Разработать многопоточное консольное приложение на языке C/C++ под Linux,</text>
        <text x="24" y="86" fill="#334155" font-size="13">моделирующее классическую задачу синхронизации потоков согласно варианту №7.</text>
        <text x="24" y="106" fill="#334155" font-size="13">Использовать библиотеку pthread: мьютексы pthread_mutex_t и условные переменные.</text>
        
        <text x="24" y="146" fill="#0F172A" font-size="14" font-weight="700">Критерии оценивания (максимум 10 баллов):</text>
        <text x="24" y="172" fill="#475569" font-size="13">• Корректная компиляция с ключами -Wall -Wextra -pthread (2 балла)</text>
        <text x="24" y="194" fill="#475569" font-size="13">• Отсутствие состояния гонки (Race Condition) под Valgrind/Helgrind (3 балла)</text>
        <text x="24" y="216" fill="#475569" font-size="13">• Оформленный текстовый отчёт с блок-схемами и выводами (3 балла)</text>
        <text x="24" y="238" fill="#475569" font-size="13">• Защита работы и ответы на контрольные вопросы (2 балла)</text>
        
        <text x="24" y="284" fill="#0F172A" font-size="14" font-weight="700">📎 Методические материалы (MinIO S3):</text>
        
        <!-- File Item 1 -->
        <g transform="translate(24, 304)">
          <rect width="632" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
          <rect x="16" y="12" width="36" height="36" rx="6" fill="#FEE2E2" />
          <text x="34" y="34" fill="#DC2626" font-size="11" font-weight="800" text-anchor="middle">PDF</text>
          <text x="64" y="28" fill="#0F172A" font-size="13" font-weight="600">Методические_указания_ЛР3_ОС_2026.pdf</text>
          <text x="64" y="44" fill="#64748B" font-size="11">Размер: 2.4 МБ • Загружено: 15.10.2026</text>
          <rect x="520" y="14" width="96" height="32" rx="6" fill="#FFFFFF" stroke="#CBD5E1" />
          <text x="568" y="34" fill="#1E293B" font-size="12" font-weight="600" text-anchor="middle">Скачать ↓</text>
        </g>
        
        <!-- File Item 2 -->
        <g transform="translate(24, 376)">
          <rect width="632" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
          <rect x="16" y="12" width="36" height="36" rx="6" fill="#DBEAFE" />
          <text x="34" y="34" fill="#2563EB" font-size="11" font-weight="800" text-anchor="middle">ZIP</text>
          <text x="64" y="28" fill="#0F172A" font-size="13" font-weight="600">Исходные_шаблоны_кода_var7.zip</text>
          <text x="64" y="44" fill="#64748B" font-size="11">Размер: 450 КБ • SHA-256 проверен</text>
          <rect x="520" y="14" width="96" height="32" rx="6" fill="#FFFFFF" stroke="#CBD5E1" />
          <text x="568" y="34" fill="#1E293B" font-size="12" font-weight="600" text-anchor="middle">Скачать ↓</text>
        </g>
        
        <!-- Workflow Alert: Starosta Verification Required -->
        <g transform="translate(24, 460)">
          <rect width="632" height="84" rx="8" fill="#EFF6FF" stroke="#BFDBFE" />
          <text x="20" y="28" fill="#1E40AF" font-size="13" font-weight="700">ℹ️ Регламент проверки и статус «Зачтено»:</text>
          <text x="20" y="48" fill="#1E3A8A" font-size="12">После загрузки файлов переведите работу в статус «Сдано на проверку».</text>
          <text x="20" y="66" fill="#1E3A8A" font-size="12">Официальный статус «Зачтено» выставляет исключительно староста группы</text>
          <text x="20" y="80" fill="#1E3A8A" font-size="12">после сверки с официальной ведомостью преподавателя.</text>
        </g>
      </g>
      
      <!-- Right: Secure Submission Box -->
      <g id="SubmissionBox" transform="translate(704, 0)" filter="url(#card-shadow)">
        <rect width="412" height="574" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
        
        <text x="24" y="36" fill="#0F172A" font-size="16" font-weight="700">📤 Форма сдачи решения</text>
        
        <!-- Status Switcher -->
        <g transform="translate(24, 52)">
          <text x="0" y="16" fill="#64748B" font-size="12" font-weight="600">ТЕКУЩИЙ СТАТУС ВЫПОЛНЕНИЯ:</text>
          <rect y="26" width="364" height="40" rx="8" fill="#F1F5F9" stroke="#E2E8F0" />
          <rect x="4" y="30" width="114" height="32" rx="6" fill="#FFFFFF" />
          <text x="61" y="50" fill="#0F172A" font-size="12" font-weight="700" text-anchor="middle">В процессе</text>
          
          <rect x="122" y="30" width="116" height="32" rx="6" fill="#EF4444" />
          <text x="180" y="50" fill="#FFFFFF" font-size="12" font-weight="700" text-anchor="middle">Сдать на проверку</text>
          
          <text x="298" y="50" fill="#94A3B8" font-size="12" font-weight="500" text-anchor="middle">Зачтено 🔒</text>
        </g>
        
        <!-- Dropzone for Safe Archive Upload -->
        <g id="Dropzone" transform="translate(24, 146)">
          <rect width="364" height="154" rx="10" fill="#F8FAFC" stroke="#818CF8" stroke-width="2" stroke-dasharray="6 6" />
          <text x="182" y="54" font-size="28" text-anchor="middle">📁</text>
          <text x="182" y="84" fill="#0F172A" font-size="14" font-weight="700" text-anchor="middle">Перетащите архив решения сюда</text>
          <text x="182" y="104" fill="#64748B" font-size="12" text-anchor="middle">ZIP, RAR до 50 МБ (распаковка до 200 МБ)</text>
          
          <rect x="122" y="116" width="120" height="26" rx="6" fill="#4F46E5" />
          <text x="182" y="133" fill="#FFFFFF" font-size="11" font-weight="600" text-anchor="middle">Выбрать файл</text>
        </g>
        
        <!-- Attached File with Antivirus & Zip-Bomb check -->
        <g id="AttachedFile" transform="translate(24, 314)">
          <rect width="364" height="74" rx="8" fill="#F0FDF4" stroke="#86EFAC" />
          <text x="16" y="24" fill="#166534" font-size="12" font-weight="700">✓ kaberdin_os_lab3_var7.zip (1.8 МБ)</text>
          <text x="16" y="44" fill="#15803D" font-size="11">🛡 Антивирус: CLEAN • Исполняемых файлов (.exe/.sh): 0</text>
          <text x="16" y="60" fill="#15803D" font-size="11">🛡 Zip-Bomb защита: Коэффициент сжатия 4:1 (норма)</text>
          <text x="334" y="26" fill="#DC2626" font-size="14">✕</text>
        </g>
        
        <!-- Notes text field -->
        <g transform="translate(24, 404)">
          <text x="0" y="14" fill="#64748B" font-size="12" font-weight="600">КОММЕНТАРИЙ СТАРОСТЕ / ПРЕПОДАВАТЕЛЮ:</text>
          <rect y="22" width="364" height="66" rx="8" fill="#F8FAFC" stroke="#CBD5E1" />
          <text x="12" y="44" fill="#475569" font-size="12">В архиве лежит исходный код main.c и отчёт.pdf с</text>
          <text x="12" y="62" fill="#475569" font-size="12">результатами замеров времени выполнения.</text>
        </g>
        
        <!-- Submit Button -->
        <rect x="24" y="504" width="364" height="46" rx="8" fill="#4F46E5" />
        <text x="206" y="532" fill="#FFFFFF" font-size="14" font-weight="700" text-anchor="middle">Отправить на проверку старосте</text>
      </g>
    </g>
  </g>
"""
    return get_svg_wrapper(1440, 900, "03_Карточка_Задания_и_Сдача", content)

# Screen 4: Starosta Analytics Performance Matrix
def create_analytics_matrix_svg():
    sidebar = render_sidebar("analytics", is_starosta=True)
    header = render_header("Сводная матрица успеваемости группы 921701", "Режим Старосты • Мониторинг задолженностей и верификация статусов", "📥 Экспорт ведомости")
    
    content = f"""{sidebar}
{header}
  <g id="MatrixContent" transform="translate(292, 96)">
    <!-- Top Filter & KPI Bar -->
    <g id="KpiRow" filter="url(#card-shadow)">
      <rect width="1116" height="96" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
      
      <!-- Filter 1: Subject -->
      <g transform="translate(24, 28)">
        <text x="0" y="12" fill="#64748B" font-size="11" font-weight="600">ДИСЦИПЛИНА:</text>
        <rect y="18" width="200" height="36" rx="6" fill="#F1F5F9" stroke="#CBD5E1" />
        <text x="14" y="41" fill="#0F172A" font-size="13" font-weight="600">Все дисциплины (4)</text>
        <text x="180" y="41" fill="#64748B" font-size="12">▼</text>
      </g>
      
      <!-- Filter 2: Subgroup -->
      <g transform="translate(244, 28)">
        <text x="0" y="12" fill="#64748B" font-size="11" font-weight="600">ПОДГРУППА:</text>
        <rect y="18" width="160" height="36" rx="6" fill="#F1F5F9" stroke="#CBD5E1" />
        <text x="14" y="41" fill="#0F172A" font-size="13" font-weight="600">Все студенты (25)</text>
        <text x="140" y="41" fill="#64748B" font-size="12">▼</text>
      </g>
      
      <!-- Metric: Verified Percentage -->
      <g transform="translate(440, 20)">
        <text x="0" y="16" fill="#64748B" font-size="11" font-weight="600">ОБЩИЙ % СДАЧИ:</text>
        <text x="0" y="48" fill="#10B981" font-size="28" font-weight="800">74.2%</text>
        <rect x="94" y="28" width="140" height="8" rx="4" fill="#E2E8F0" />
        <rect x="94" y="28" width="104" height="8" rx="4" fill="#10B981" />
      </g>
      
      <!-- Action: Needs Verification Count -->
      <g transform="translate(710, 24)">
        <rect width="180" height="48" rx="8" fill="#FEF3C7" stroke="#FDE68A" />
        <text x="16" y="22" fill="#92400E" font-size="11" font-weight="700">ОЖИДАЮТ ПРОВЕРКИ:</text>
        <text x="16" y="40" fill="#B45309" font-size="16" font-weight="800">6 работ старосте</text>
      </g>
      
      <!-- Export Buttons -->
      <g transform="translate(910, 28)">
        <rect width="90" height="40" rx="6" fill="#059669" />
        <text x="45" y="25" fill="#FFFFFF" font-size="12" font-weight="700" text-anchor="middle">Excel (.xlsx)</text>
        
        <rect x="98" y="0" width="84" height="40" rx="6" fill="#DC2626" />
        <text x="140" y="25" fill="#FFFFFF" font-size="12" font-weight="700" text-anchor="middle">PDF Отчёт</text>
      </g>
    </g>
    
    <!-- Matrix Table Card -->
    <g id="MatrixTable" transform="translate(0, 116)" filter="url(#card-shadow)">
      <rect width="1116" height="638" rx="12" fill="#FFFFFF" stroke="#E2E8F0" />
      
      <!-- Table Header -->
      <rect x="0" y="0" width="1116" height="48" rx="12" fill="#F8FAFC" />
      <text x="24" y="28" fill="#475569" font-size="12" font-weight="700">№</text>
      <text x="56" y="28" fill="#475569" font-size="12" font-weight="700">СТУДЕНТ (ФИО)</text>
      <text x="260" y="28" fill="#475569" font-size="12" font-weight="700">ПГ</text>
      <text x="320" y="28" fill="#475569" font-size="12" font-weight="700">ОС • ЛР №1</text>
      <text x="440" y="28" fill="#475569" font-size="12" font-weight="700">ОС • ЛР №2</text>
      <text x="560" y="28" fill="#475569" font-size="12" font-weight="700">ОС • ЛР №3</text>
      <text x="680" y="28" fill="#475569" font-size="12" font-weight="700">СПО • ПР №4</text>
      <text x="800" y="28" fill="#475569" font-size="12" font-weight="700">БД • КР Эскиз</text>
      <text x="940" y="28" fill="#475569" font-size="12" font-weight="700">ДОЛГИ</text>
      <text x="1020" y="28" fill="#475569" font-size="12" font-weight="700">ДЕЙСТВИЯ</text>
      <line x1="0" y1="48" x2="1116" y2="48" stroke="#E2E8F0" />
"""
    # Matrix rows
    students = [
        (1, "Кабердин Данила", "1", "PASS", "PASS", "IN_PROGRESS", "PASS", "PENDING_VERIFY", "0"),
        (2, "Кахнович Владислав", "1", "PASS", "PASS", "PASS", "PASS", "PASS", "0"),
        (3, "Киселёв Владислав", "2", "PASS", "PASS", "IN_PROGRESS", "PENDING_VERIFY", "PASS", "0"),
        (4, "Алексеев Максим", "1", "PASS", "PASS", "OVERDUE", "PASS", "NOT_STARTED", "1"),
        (5, "Борисова Екатерина", "2", "PASS", "PASS", "PASS", "PASS", "PASS", "0"),
        (6, "Волков Артём", "1", "PASS", "PENDING_VERIFY", "OVERDUE", "NOT_STARTED", "OVERDUE", "2"),
        (7, "Дмитриев Илья", "2", "PASS", "PASS", "IN_PROGRESS", "PASS", "PASS", "0"),
        (8, "Зайцев Михаил", "1", "PASS", "PASS", "PASS", "PASS", "PENDING_VERIFY", "0"),
    ]
    
    def render_cell(status, x, y):
        if status == "PASS":
            return f"""<rect x="{x}" y="{y}" width="96" height="30" rx="6" fill="#DCFCE7" />
<text x="{x+48}" y="{y+19}" fill="#166534" font-size="11" font-weight="700" text-anchor="middle">✓ Зачтено</text>"""
        elif status == "PENDING_VERIFY":
            return f"""<rect x="{x}" y="{y}" width="96" height="30" rx="6" fill="#FEF3C7" stroke="#F59E0B" stroke-width="1.5" />
<text x="{x+48}" y="{y+19}" fill="#92400E" font-size="10" font-weight="700" text-anchor="middle">⏳ Проверить</text>"""
        elif status == "IN_PROGRESS":
            return f"""<rect x="{x}" y="{y}" width="96" height="30" rx="6" fill="#EFF6FF" />
<text x="{x+48}" y="{y+19}" fill="#1E40AF" font-size="11" font-weight="600" text-anchor="middle">В работе</text>"""
        elif status == "OVERDUE":
            return f"""<rect x="{x}" y="{y}" width="96" height="30" rx="6" fill="#FEE2E2" />
<text x="{x+48}" y="{y+19}" fill="#991B1B" font-size="11" font-weight="700" text-anchor="middle">✕ Долг</text>"""
        else: # NOT_STARTED
            return f"""<rect x="{x}" y="{y}" width="96" height="30" rx="6" fill="#F1F5F9" />
<text x="{x+48}" y="{y+19}" fill="#64748B" font-size="11" font-weight="500" text-anchor="middle">—</text>"""

    for idx, (num, name, pg, s1, s2, s3, s4, s5, debts) in enumerate(students):
        row_y = 56 + idx * 56
        bg_row = "#F8FAFC" if idx % 2 == 1 else "#FFFFFF"
        content += f"""      <!-- Row {num}: {name} -->
      <rect x="0" y="{row_y - 8}" width="1116" height="56" fill="{bg_row}" />
      <text x="24" y="{row_y + 24}" fill="#64748B" font-size="12">{num}</text>
      <text x="56" y="{row_y + 24}" fill="#0F172A" font-size="13" font-weight="600">{name}</text>
      <text x="264" y="{row_y + 24}" fill="#64748B" font-size="12">ПГ-{pg}</text>
      
      {render_cell(s1, 310, row_y + 4)}
      {render_cell(s2, 430, row_y + 4)}
      {render_cell(s3, 550, row_y + 4)}
      {render_cell(s4, 670, row_y + 4)}
      {render_cell(s5, 790, row_y + 4)}
      
      <text x="955" y="{row_y + 24}" fill="{'#DC2626' if debts != '0' else '#10B981'}" font-size="14" font-weight="700">{debts}</text>
      
      <rect x="1016" y="{row_y + 4}" width="76" height="30" rx="6" fill="#4F46E5" />
      <text x="1054" y="{row_y + 23}" fill="#FFFFFF" font-size="11" font-weight="600" text-anchor="middle">Карта →</text>
      <line x1="0" y1="{row_y + 48}" x2="1116" y2="{row_y + 48}" stroke="#E2E8F0" />
"""

    # Legend at bottom
    content += f"""      <g transform="translate(24, 580)">
        <text x="0" y="24" fill="#64748B" font-size="12" font-weight="600">ОБОЗНАЧЕНИЯ:</text>
        <rect x="110" y="8" width="18" height="18" rx="4" fill="#DCFCE7" />
        <text x="134" y="22" fill="#166534" font-size="12">Зачтено (подтверждено старостой)</text>
        
        <rect x="360" y="8" width="18" height="18" rx="4" fill="#FEF3C7" stroke="#F59E0B" />
        <text x="384" y="22" fill="#92400E" font-size="12">Сдано на проверку (требует верификации)</text>
        
        <rect x="650" y="8" width="18" height="18" rx="4" fill="#EFF6FF" />
        <text x="674" y="22" fill="#1E40AF" font-size="12">В процессе</text>
        
        <rect x="770" y="8" width="18" height="18" rx="4" fill="#FEE2E2" />
        <text x="794" y="22" fill="#991B1B" font-size="12">Просрочено (академический долг)</text>
      </g>
    </g>
  </g>
"""
    return get_svg_wrapper(1440, 900, "04_Сводная_Матрица_Успеваемости_Старосты", content)

# Screen 5: Verification Modal (Starosta Workflow)
def create_verification_modal_svg():
    # Base background: Analytics matrix dimmed
    base_screen = create_analytics_matrix_svg()
    # Strip </svg>
    base_clean = base_screen[:base_screen.rfind("</svg>")]
    
    modal_content = f"""
  <!-- Dark Backdrop Overlay -->
  <g id="ModalOverlay">
    <rect width="1440" height="900" fill="#0F172A" fill-opacity="0.65" />
    
    <!-- Modal Dialog Window (640 x 620, Centered) -->
    <g id="VerificationDialog" transform="translate(400, 140)" filter="url(#modal-shadow)">
      <rect width="640" height="620" rx="16" fill="#FFFFFF" />
      
      <!-- Modal Header -->
      <g transform="translate(32, 32)">
        <rect width="40" height="40" rx="10" fill="#EEF2FF" />
        <text x="20" y="26" fill="#4F46E5" font-size="20" text-anchor="middle">✓</text>
        
        <text x="56" y="22" fill="#0F172A" font-size="18" font-weight="700">Верификация сдачи лабораторной работы</text>
        <text x="56" y="40" fill="#64748B" font-size="12">Двухэтапный контроль: подтверждение статуса по ведомости преподавателя</text>
        <text x="576" y="20" fill="#94A3B8" font-size="18">✕</text>
      </g>
      
      <line x1="0" y1="90" x2="640" y2="90" stroke="#E2E8F0" />
      
      <!-- Submission Metadata Box -->
      <g transform="translate(32, 110)">
        <rect width="576" height="136" rx="10" fill="#F8FAFC" stroke="#E2E8F0" />
        
        <text x="20" y="28" fill="#64748B" font-size="11" font-weight="700">СТУДЕНТ:</text>
        <text x="20" y="48" fill="#0F172A" font-size="15" font-weight="700">Кабердин Данила (Группа 921701 • ПГ-1)</text>
        
        <text x="320" y="28" fill="#64748B" font-size="11" font-weight="700">ДИСЦИПЛИНА И РАБОТА:</text>
        <text x="320" y="48" fill="#0F172A" font-size="15" font-weight="700">ОС • Лабораторная №3 (Вариант 7)</text>
        
        <text x="20" y="80" fill="#64748B" font-size="11" font-weight="700">ДАТА ОТПРАВКИ СТУДЕНТОМ:</text>
        <text x="20" y="100" fill="#1E293B" font-size="13">24 октября 2026, 02:40 (До дедлайна оставалось 20ч)</text>
        
        <text x="320" y="80" fill="#64748B" font-size="11" font-weight="700">АРХИВ С РЕШЕНИЕМ (S3):</text>
        <text x="320" y="100" fill="#4F46E5" font-size="13" font-weight="600">📎 kaberdin_os_lab3_var7.zip (1.8 МБ)</text>
        <text x="320" y="118" fill="#10B981" font-size="11">✓ Проверен антивирусом: угроз нет</text>
      </g>
      
      <!-- Radio Selection: Starosta Decision -->
      <g transform="translate(32, 270)">
        <text x="0" y="16" fill="#0F172A" font-size="14" font-weight="700">Выберите решение старосты:</text>
        
        <!-- Option 1: PASSED (Selected) -->
        <g transform="translate(0, 30)">
          <rect width="576" height="54" rx="8" fill="#F0FDF4" stroke="#22C55E" stroke-width="2" />
          <circle cx="28" cy="27" r="10" fill="#22C55E" />
          <circle cx="28" cy="27" r="4" fill="#FFFFFF" />
          <text x="50" y="28" fill="#15803D" font-size="14" font-weight="700">Зачтено (Подтверждено преподавателем)</text>
          <text x="50" y="44" fill="#166534" font-size="11">Работа будет отмечена как успешно сданная во всех сводках и матрице группы</text>
        </g>
        
        <!-- Option 2: REVISION -->
        <g transform="translate(0, 94)">
          <rect width="576" height="54" rx="8" fill="#FFFBEB" stroke="#CBD5E1" />
          <circle cx="28" cy="27" r="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2" />
          <text x="50" y="28" fill="#92400E" font-size="14" font-weight="700">На доработку (Требуются исправления)</text>
          <text x="50" y="44" fill="#78350F" font-size="11">Студенту будет отправлено уведомление с замечаниями преподавателя</text>
        </g>
        
        <!-- Option 3: REJECTED -->
        <g transform="translate(0, 158)">
          <rect width="576" height="54" rx="8" fill="#FEF2F2" stroke="#CBD5E1" />
          <circle cx="28" cy="27" r="10" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2" />
          <text x="50" y="28" fill="#991B1B" font-size="14" font-weight="700">Не зачтено (Аннулировано / Плагиат)</text>
          <text x="50" y="44" fill="#7F1D1D" font-size="11">Работа аннулируется, статус переходит в долг</text>
        </g>
      </g>
      
      <!-- Grade & Comments -->
      <g transform="translate(32, 500)">
        <text x="0" y="14" fill="#64748B" font-size="12" font-weight="600">ОЦЕНКА ПРЕПОДАВАТЕЛЯ / ЗАМЕТКА:</text>
        <rect y="22" width="576" height="38" rx="6" fill="#F8FAFC" stroke="#CBD5E1" />
        <text x="12" y="46" fill="#0F172A" font-size="13">10 из 10 баллов (Защита принята 24.10, замечаний нет)</text>
      </g>
      
      <!-- Buttons -->
      <g transform="translate(32, 566)">
        <rect width="180" height="42" rx="8" fill="#F1F5F9" />
        <text x="90" y="26" fill="#475569" font-size="13" font-weight="600" text-anchor="middle">Отмена</text>
        
        <rect x="376" y="0" width="200" height="42" rx="8" fill="#10B981" />
        <text x="476" y="26" fill="#FFFFFF" font-size="13" font-weight="700" text-anchor="middle">Подтвердить статус «Зачтено»</text>
      </g>
    </g>
  </g>
</svg>"""
    return base_clean + modal_content

# Screen 6: Auth & Invite Code Registration (Brute-Force & Belarus Law)
def create_auth_register_svg():
    return f"""<svg width="1440" height="900" viewBox="0 0 1440 900" fill="none" xmlns="http://www.w3.org/2000/svg" {FONT}>
  <defs>
    <filter id="auth-shadow" x="-10" y="-5" width="115%" height="115%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#0F172A" flood-opacity="0.1" />
    </filter>
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#EEF2FF" />
      <stop offset="100%" stop-color="#E0E7FF" />
    </linearGradient>
  </defs>
  
  <rect width="1440" height="900" fill="url(#bg-grad)" />
  
  <!-- Left Side: Promo & Benefits -->
  <g id="PromoSection" transform="translate(140, 200)">
    <rect width="48" height="48" rx="12" fill="#4F46E5" />
    <text x="24" y="32" fill="#FFFFFF" font-size="24" text-anchor="middle">⏱</text>
    
    <text x="0" y="90" fill="#0F172A" font-size="34" font-weight="900">StudyPulse</text>
    <text x="0" y="126" fill="#4F46E5" font-size="18" font-weight="700">Учёт заданий и дедлайнов учебной группы</text>
    
    <text x="0" y="174" fill="#334155" font-size="15">• Единое расписание сроков без потерь в чатах</text>
    <text x="0" y="206" fill="#334155" font-size="15">• Детерминированное закрепление вариантов заданий</text>
    <text x="0" y="238" fill="#334155" font-size="15">• Официальная верификация старостой статуса «Зачтено»</text>
    <text x="0" y="270" fill="#334155" font-size="15">• Интеллектуальный календарь с подсчётом дней пиковой нагрузки</text>
    
    <!-- Law Compliance Box -->
    <g transform="translate(0, 330)">
      <rect width="440" height="86" rx="10" fill="#FFFFFF" stroke="#CBD5E1" />
      <text x="20" y="30" fill="#059669" font-size="13" font-weight="700">🛡 Безопасность и защита персональных данных</text>
      <text x="20" y="52" fill="#64748B" font-size="12">Сервис разработан в строгом соответствии с Законом</text>
      <text x="20" y="70" fill="#64748B" font-size="12">Республики Беларусь от 7 мая 2021 г. № 99-З.</text>
    </g>
  </g>
  
  <!-- Right Side: Registration / Invite Auth Card (480 x 680) -->
  <g id="AuthCard" transform="translate(760, 110)" filter="url(#auth-shadow)">
    <rect width="480" height="680" rx="16" fill="#FFFFFF" />
    
    <!-- Tabs: [Вход] / [Регистрация по инвайту] -->
    <g transform="translate(36, 32)">
      <rect width="408" height="44" rx="8" fill="#F1F5F9" />
      
      <rect x="4" y="4" width="198" height="36" rx="6" fill="#FFFFFF" />
      <text x="103" y="27" fill="#0F172A" font-size="13" font-weight="700" text-anchor="middle">Вход в систему</text>
      
      <rect x="206" y="4" width="198" height="36" rx="6" fill="#4F46E5" />
      <text x="305" y="27" fill="#FFFFFF" font-size="13" font-weight="700" text-anchor="middle">Регистрация по инвайту</text>
    </g>
    
    <!-- Form Fields -->
    <g transform="translate(36, 102)">
      <!-- Field 1: Invite Code -->
      <g>
        <text x="0" y="14" fill="#0F172A" font-size="12" font-weight="700">ИНВАЙТ-КОД ГРУППЫ (ОТ СТАРОСТЫ):</text>
        <rect y="22" width="408" height="44" rx="8" fill="#F8FAFC" stroke="#818CF8" stroke-width="2" />
        <text x="14" y="50" fill="#4F46E5" font-size="14" font-weight="700">GRP-921701-X8F9</text>
        <text x="350" y="50" fill="#10B981" font-size="12" font-weight="700">✓ Найдена</text>
        
        <rect y="72" width="408" height="32" rx="6" fill="#F0FDF4" />
        <text x="12" y="92" fill="#166534" font-size="11" font-weight="600">Группа: 921701 • ФКСиС • 2026/2027 уч. год</text>
      </g>
      
      <!-- Field 2: Full Name -->
      <g transform="translate(0, 116)">
        <text x="0" y="14" fill="#0F172A" font-size="12" font-weight="700">ФИО СТУДЕНТА (КАК В ЗАЧЁТКЕ):</text>
        <rect y="22" width="408" height="42" rx="8" fill="#F8FAFC" stroke="#CBD5E1" />
        <text x="14" y="48" fill="#0F172A" font-size="13">Кабердин Данила Сергеевич</text>
      </g>
      
      <!-- Field 3: Subgroup -->
      <g transform="translate(0, 192)">
        <text x="0" y="14" fill="#0F172A" font-size="12" font-weight="700">ПОДГРУППА:</text>
        <rect y="22" width="408" height="42" rx="8" fill="#F8FAFC" stroke="#CBD5E1" />
        <text x="14" y="48" fill="#0F172A" font-size="13">Подгруппа №1</text>
        <text x="380" y="48" fill="#64748B" font-size="12">▼</text>
      </g>
      
      <!-- Field 4: Email & Password -->
      <g transform="translate(0, 268)">
        <text x="0" y="14" fill="#0F172A" font-size="12" font-weight="700">EMAIL И ПАРОЛЬ:</text>
        <rect y="22" width="408" height="42" rx="8" fill="#F8FAFC" stroke="#CBD5E1" />
        <text x="14" y="48" fill="#0F172A" font-size="13">danila.kaberdin@bsuir.by</text>
        
        <rect y="72" width="408" height="42" rx="8" fill="#F8FAFC" stroke="#CBD5E1" />
        <text x="14" y="98" fill="#64748B" font-size="13">••••••••••••••••</text>
      </g>
      
      <!-- Anti-Brute-Force Notice -->
      <g transform="translate(0, 396)">
        <rect width="408" height="50" rx="6" fill="#FEF3C7" stroke="#FDE68A" />
        <text x="12" y="20" fill="#92400E" font-size="11" font-weight="700">🔒 Ступенчатая защита от брутфорса:</text>
        <text x="12" y="38" fill="#78350F" font-size="11">5 неверных попыток → CAPTCHA; 10 попыток → блок на 15 мин.</text>
      </g>
      
      <!-- Consent Checkbox -->
      <g transform="translate(0, 460)">
        <rect width="18" height="18" rx="4" fill="#4F46E5" />
        <text x="9" y="14" fill="#FFFFFF" font-size="12" text-anchor="middle">✓</text>
        <text x="28" y="14" fill="#475569" font-size="11">Даю согласие на обработку персональных данных (ФИО,</text>
        <text x="28" y="28" fill="#475569" font-size="11">успеваемость) согласно Закону РБ № 99-З</text>
      </g>
      
      <!-- Submit Button -->
      <rect y="504" width="408" height="46" rx="8" fill="#4F46E5" />
      <text x="204" y="532" fill="#FFFFFF" font-size="14" font-weight="700" text-anchor="middle">Зарегистрироваться в группе</text>
    </g>
  </g>
</svg>"""

def main():
    out_dir = r"c:\Users\kaber\Desktop\СПО\Макеты_Figma"
    os.makedirs(out_dir, exist_ok=True)
    
    files = {
        "01_dashboard.svg": create_dashboard_svg(),
        "02_calendar.svg": create_calendar_svg(),
        "03_task_details.svg": create_task_details_svg(),
        "04_analytics_matrix.svg": create_analytics_matrix_svg(),
        "05_verification_modal.svg": create_verification_modal_svg(),
        "06_auth_register.svg": create_auth_register_svg(),
    }
    
    for filename, content in files.items():
        filepath = os.path.join(out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {filepath} ({len(content)} bytes)")

if __name__ == "__main__":
    main()
