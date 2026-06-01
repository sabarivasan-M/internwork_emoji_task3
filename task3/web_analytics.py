"""
Web Traffic Analytics
Computes key metrics, user journeys, drop-off points, and simple funnel analysis.
"""
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

class WebAnalytics:
    def __init__(self, sessions_file):
        self.df = pd.read_csv(sessions_file)
        # parse page sequences
        self.df['page_sequence_list'] = self.df['page_sequence'].fillna('').apply(lambda s: s.split('|') if s else [])

    def summary_metrics(self):
        total_sessions = len(self.df)
        total_pageviews = self.df['page_views'].sum()
        avg_session_duration = self.df['session_duration_s'].mean()
        median_session_duration = self.df['session_duration_s'].median()
        bounce_rate = self.df['bounce'].mean()
        conversion_rate = self.df['conversion'].mean()

        print('\n=== SUMMARY METRICS ===')
        print(f'Total sessions: {total_sessions:,}')
        print(f'Total pageviews: {total_pageviews:,}')
        print(f'Avg session duration (s): {avg_session_duration:.1f}')
        print(f'Median session duration (s): {median_session_duration:.1f}')
        print(f'Bounce rate: {bounce_rate*100:.2f}%')
        print(f'Conversion rate: {conversion_rate*100:.2f}%')

        return {
            'total_sessions': total_sessions,
            'total_pageviews': total_pageviews,
            'avg_session_duration_s': avg_session_duration,
            'median_session_duration_s': median_session_duration,
            'bounce_rate': bounce_rate,
            'conversion_rate': conversion_rate
        }

    def top_pages(self, n=20):
        pages = Counter()
        for seq in self.df['page_sequence_list']:
            for p in seq:
                pages[p]+=1
        top = pages.most_common(n)
        print('\n=== TOP PAGES ===')
        for p,c in top:
            print(f'  {p}: {c}')
        return top

    def exit_rates(self):
        exits = Counter(self.df['exit_page'])
        starts = Counter(self.df['entry_page'])
        print('\n=== EXIT PAGES (top 20) ===')
        for p,c in exits.most_common(20):
            total_visits = sum(1 for seq in self.df['page_sequence_list'] if p in seq)
            rate = c/total_visits if total_visits>0 else 0
            print(f'  {p}: exits={c}, visits={total_visits}, exit_rate={rate:.2f}')
        return exits

    def transition_matrix(self, top_n=30):
        trans = defaultdict(Counter)
        for seq in self.df['page_sequence_list']:
            for a,b in zip(seq, seq[1:]):
                trans[a][b]+=1
        print('\n=== TRANSITION SAMPLE ===')
        for a, neigh in list(trans.items())[:20]:
            total = sum(neigh.values())
            probs = [(b, cnt/total) for b,cnt in neigh.items() for b in [b]]
            print(f'  {a} -> {dict(neigh)}')
        return trans

    def common_journeys(self, n=10):
        journey_counts = Counter(self.df['page_sequence'])
        print('\n=== COMMON JOURNEYS ===')
        for seq, cnt in journey_counts.most_common(n):
            print(f'  {cnt} sessions: {seq}')
        return journey_counts.most_common(n)

    def funnel_analysis(self, funnel_steps=['/','/pricing','/signup']):
        print('\n=== FUNNEL ANALYSIS ===')
        total = 0
        current_sessions = set(self.df['session_id'])
        for step in funnel_steps:
            has_step = set(self.df[self.df['page_sequence'].str.contains(step)]['session_id'])
            count = len(has_step)
            print(f'  Step: {step} — {count} sessions ({count/len(self.df)*100:.2f}%)')
        return True

    def detect_dropoff_points(self):
        # compute fraction of sessions that exit at each step position
        pos_exits = Counter()
        pos_visits = Counter()
        for seq in self.df['page_sequence_list']:
            for i,p in enumerate(seq):
                pos_visits[i]+=1
            if seq:
                pos_exits[len(seq)-1]+=1
        print('\n=== DROPOFF BY POSITION ===')
        for pos in sorted(pos_visits.keys()):
            exits = pos_exits.get(pos,0)
            visits = pos_visits[pos]
            print(f'  Position {pos+1}: visits={visits}, exits={exits}, exit_rate={exits/visits:.2f}')
        return True

    def run_all(self):
        report = {}
        report['summary'] = self.summary_metrics()
        report['top_pages'] = self.top_pages(20)
        report['exits'] = self.exit_rates()
        report['transitions'] = self.transition_matrix()
        report['journeys'] = self.common_journeys(15)
        report['funnel'] = self.funnel_analysis()
        report['dropoffs'] = self.detect_dropoff_points()
        return report

if __name__ == '__main__':
    infile = r"c:\Users\HP\Music\data_anal_inter\task3\web_traffic_sessions.csv"
    wa = WebAnalytics(infile)
    wa.run_all()
