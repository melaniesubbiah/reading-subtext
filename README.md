# Evaluating LLM Short Story Summarization with Writers
Code and data for this paper: [Reading Subtext: Evaluating Large Language Models on Short Story Summarization with Writers](https://arxiv.org/pdf/2403.01061.pdf)

Annotations of faithfulness errors along with the errors themselves can be found under 'error_annotations'.

Scripts to have models generate summaries, score summaries, and label faithfulness errors are in 'model_scripts'. The generated summary scores are saved in 'summary_scores' and the error labels are in 'error_annotations'.

The interface for writers to evaluate summaries is in 'streamlit_interface'.

The 'Paper_Results' notebook has code for tables in the paper.

The writer assigned scores, feedback, and story types are in 'writer_ratings_comments.tsv' and 'story_labels.json'.
