#Idea - Compare emotion analysis of report & Q&A over time

1) Separate the report and Q&A -  the former will be scripted and the latter is more conversational
2) Conduct emotion analysis on each & compare (I would expect the report to be more "positive" than the Q&A)
3) Compare to previous quarters over 2-3 years and investigate any explanations (geopolitical etc)
4) Create a profile for each bank
5) Create a dashboard and highlight changes (large = red/ medium = orange/ small = green)
6) Compare multiple banks for "unusual" changes - flag for risk review


project_setup file contains only the code needed to connect to the raw data
initial_eda is just a quick check of the contents

-------------
Bertopic - couldn't get this to work. Renamed as old_bertopic and may revisit later

-------------
First attempt - now called old_bert_emotion
Issues with plotting last sentence analysed rather than average

21/09/2026
Second attempt - bert_emotion_ubs
Gives positive emotions (Joy & Love), negative emotions (fear, anger & sadness) plus surprise (which could be either)
"Surprise" aligns with annoucement of merger in Q2 2023

22/9/2026
Completed JPM analysis using Bertemotion - details in final summary tally with JPM performance
Issue is the terminology = "love" is an odd word to describe the financial industry
There is proven overlap with "joy" and so could they be combined into "happiness" ? - or is this the same as "positive sentiment in Finbert


23/9/26
Test theory using FinBert model and UBS data - does this reduce the information too far?
Yes - the only sentiment that it picks up is the negative emotion in the Q&A than the presentation in Q3 2024
Repeat with JPM to check effects

Remove speaker names from sentence text by collecting as a list, splitting into first name & surname and removing capitals
Add this list to the pre-processing function then removes them before creating the "cleaned_text" column
Checked both models (Bert Emotion & FinBert) for both datasets (UBS and JPM)

Saved final timeline figures but still think that there may be a better way to present this data


25/09/2026
Attempt to split UBS by speaker to see who is creating the positive vibes !