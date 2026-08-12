import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv() 

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'mojabaza')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

plt.rcParams['font.family'] = 'monospace'
fig_bg = '#0d1117'
ax_bg = '#161b22'
text_c = '#c9d1d9'

print("Generowanie wykresu 1: Dzielnice...")
df = pd.read_sql('SELECT * FROM etl.vw_borough_stats', engine)

fig, ax = plt.subplots(figsize=(10, 6), facecolor=fig_bg)
ax.set_facecolor(ax_bg)
bars = ax.bar(df['borough_name'], df['total_requests'], 
              color=['#1f6feb', '#238636', '#d29922', '#8957e5', '#f85149', '#8b949e'],
              edgecolor='#30363d', linewidth=1.5)
for bar, val in zip(bars, df['total_requests']):
    ax.text(bar.get_x() + bar.get_width()/2, val + 5, str(val),
            ha='center', va='bottom', color=text_c, fontsize=11, fontweight='bold')
ax.set_title('Zgłoszenia 311 per Dzielnica', fontsize=16, fontweight='bold', color='#58a6ff', pad=15)
ax.tick_params(colors=text_c, labelsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.setp(ax.xaxis.get_majorticklabels(), rotation=15, ha='right')
plt.tight_layout()
plt.savefig('chart_1_boroughs.png', dpi=150, facecolor=fig_bg)
print("  Zapisano: chart_1_boroughs.png")

print("Generowanie wykresu 2: Kategorie...")
df = pd.read_sql('SELECT * FROM etl.vw_category_stats', engine)

fig, ax = plt.subplots(figsize=(12, 9), facecolor=fig_bg)
ax.set_facecolor(fig_bg)

colors_pie = ['#f85149', '#1f6feb', '#8b949e', '#d29922', '#238636', '#8957e5', '#3fb950']

explode = [0.05 if i >= 2 else 0 for i in range(len(df))]

wedges, texts, autotexts = ax.pie(
    df['total_requests'], 
    labels=None,
    autopct='%1.1f%%',
    pctdistance=0.75,
    colors=colors_pie, 
    explode=explode, 
    startangle=90,
    textprops={'color': '#0d1117', 'fontsize': 10, 'fontweight': 'bold'},
    wedgeprops={'edgecolor': fig_bg, 'linewidth': 3}
)

legend_labels = [f"{row['category']} ({row['total_requests']})" for _, row in df.iterrows()]
ax.legend(wedges, legend_labels, 
          title="Kategorie", 
          loc="center left", 
          bbox_to_anchor=(1, 0, 0.5, 1),
          facecolor=ax_bg,
          edgecolor='#30363d',
          labelcolor=text_c,
          title_fontsize=12,
          fontsize=10)

ax.set_title('Rozkład Kategorii Zgłoszeń 311', fontsize=16, fontweight='bold', color='#58a6ff', pad=20)
plt.tight_layout()
plt.savefig('chart_2_categories.png', dpi=150, facecolor=fig_bg, bbox_inches='tight')
print("  Zapisano: chart_2_categories.png")

print("Generowanie wykresu 3: Top 10...")
df = pd.read_sql('SELECT * FROM etl.vw_top_complaints', engine)

fig, ax = plt.subplots(figsize=(12, 7), facecolor=fig_bg)
ax.set_facecolor(ax_bg)
y_pos = range(len(df))
bars = ax.barh(y_pos, df['total_requests'], color='#58a6ff', edgecolor='#30363d', height=0.6)
for bar, val in zip(bars, df['total_requests']):
    ax.text(val + 2, bar.get_y() + bar.get_height()/2, str(val),
            va='center', ha='left', color=text_c, fontsize=10, fontweight='bold')
ax.set_yticks(y_pos)
ax.set_yticklabels(df['complaint_type'], color=text_c, fontsize=10)
ax.invert_yaxis()
ax.set_title('Top 10 Typów Zgłoszeń 311', fontsize=16, fontweight='bold', color='#58a6ff', pad=15)
ax.set_xlabel('Liczba zgłoszeń', color='#8b949e', fontsize=11)
ax.tick_params(colors=text_c, labelsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('chart_3_top10.png', dpi=150, facecolor=fig_bg)
print("  Zapisano: chart_3_top10.png")

print("Generowanie wykresu 4: Statusy...")
df = pd.read_sql('SELECT * FROM etl.vw_status_distribution', engine)

fig, ax = plt.subplots(figsize=(10, 6), facecolor=fig_bg)
ax.set_facecolor(ax_bg)
colors_status = ['#238636', '#d29922', '#f85149']
bars = ax.bar(df['status'], df['total'], color=colors_status, edgecolor='#30363d', linewidth=1.5)
for bar, val in zip(bars, df['total']):
    ax.text(bar.get_x() + bar.get_width()/2, val + 5, str(val),
            ha='center', va='bottom', color=text_c, fontsize=11, fontweight='bold')
ax.set_title('Rozkład Statusów Zgłoszeń', fontsize=16, fontweight='bold', color='#58a6ff', pad=15)
ax.tick_params(colors=text_c, labelsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('chart_4_status.png', dpi=150, facecolor=fig_bg)
print("  Zapisano: chart_4_status.png")

print("\nWszystkie wykresy wygenerowane! Otwórz pliki PNG w folderze.")