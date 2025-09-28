# src/05_paper_impact_analysis.py
import pandas as pd
import numpy as np
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import os
from utils import ensure_dir

class AdvancedPaperAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.topic_model = None
        self.ml_model = None

    def load_and_preprocess(self):
        self.df = pd.read_excel(self.file_path)
        self.df.rename(columns={'영문 초록': 'abstract', 'KCI 피인용 횟수': 'citations'}, inplace=True)
        self.df['citations'] = pd.to_numeric(self.df['citations'], errors='coerce').fillna(0)
        self.df.dropna(subset=['abstract'], inplace=True)
        self.df['abstract'] = self.df['abstract'].astype(str)
        print(f"Loaded and preprocessed {len(self.df)} papers.")

    def perform_topic_modeling(self):
        docs = self.df['abstract'].tolist()
        vectorizer_model = CountVectorizer(stop_words="english")
        self.topic_model = BERTopic(vectorizer_model=vectorizer_model, verbose=True, min_topic_size=5)
        topics, _ = self.topic_model.fit_transform(docs)
        self.df['topic'] = topics
        print("Topic modeling complete.")

    def calculate_indicators(self):
        self.df['author_count'] = self.df['저자'].str.split(';').str.len().fillna(1)
        self.df['abstract_length'] = self.df['abstract'].str.len()
        self.df['year_norm'] = (self.df['논문발행연도'] - self.df['논문발행연도'].min()) / (self.df['논문발행연도'].max() - self.df['논문발행연도'].min())
        print("Indicators calculated.")

    def optimize_weights_with_ml(self):
        features = ['author_count', 'abstract_length', 'year_norm']
        target = 'citations'
        X = self.df[features]
        y = np.log1p(self.df[target])
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.ml_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.ml_model.fit(X_train, y_train)
        print(f"ML model trained. R-squared on test set: {self.ml_model.score(X_test, y_test):.2f}")
        self.feature_weights = self.ml_model.feature_importances_

    def calculate_final_impact_scores(self):
        features = ['author_count', 'abstract_length', 'year_norm']
        indicator_data = self.df[features].values
        scaled_indicators = MinMaxScaler().fit_transform(indicator_data)
        impact_score = np.dot(scaled_indicators, self.feature_weights)
        self.df['Technology_Supply_Index'] = MinMaxScaler(feature_range=(0, 100)).fit_transform(impact_score.reshape(-1, 1))
        print("Final impact scores calculated.")

    def run_analysis(self):
        self.load_and_preprocess()
        self.perform_topic_modeling()
        self.calculate_indicators()
        self.optimize_weights_with_ml()
        self.calculate_final_impact_scores()
        return self.df

def main():
    raw_path = "data/raw"
    output_path = "output/reports"
    ensure_dir(output_path)

    paper_file = os.path.join(raw_path, "academic_papers_list.xlsx")
    if not os.path.exists(paper_file):
        print(f"ERROR: Academic paper file not found at '{paper_file}'. Please provide it.")
        return

    analyzer = AdvancedPaperAnalyzer(paper_file)
    results_df = analyzer.run_analysis()
    
    output_file = os.path.join(output_path, "comprehensive_paper_analysis.xlsx")
    results_df.to_excel(output_file, index=False)
    print(f"Paper impact analysis complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()