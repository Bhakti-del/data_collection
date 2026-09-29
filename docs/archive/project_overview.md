Hey we have a data of past few (let us say 13 years) question papers data.It includes

|---|---|---|---|---|
| 1 | `subject_name` | String | `"Data Structures"` | Identifies which subject this question belongs to. Primary filter. |
| 2 | `raw_question_text` | Text | `"Explain AVL tree rotations (LL, RR, LR, RL) with an example."` | The actual question text as it appeared in the exam. |
| 3 | `topic_tag` | String | `"AVL_TREES"` | Exact concept being tested. Used for frequency-based prediction. |
| 4 | `topic_category` | String | `"SEARCH_TREES"` | Higher-level group of the topic. Used to enforce variety in OR-choice pairs. |
| 5 | `bloom_level` | Enum | `"Apply"` | Cognitive depth: `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate`. Used to balance paper difficulty. |
| 6 | `original_marks` | Integer | `7` | Standard marks for this question. Used to slot into Part A (≤3M) or Part B (≥5M). |
| 7 | `part_a_years` | List[Integer] | `[2018, 2021]` | Years this question appeared as a Part A (short answer) question. |
| 8 | `part_b_years` | List[Integer] | `[2019, 2022, 2023]` | Years this question appeared as a Part B (long answer) question. |


Now. Engine is a team who is responsible for predicting ml enginer.Frontend people are responsible for User interface for input of selecting subject and generating based on the current syllabus.The syllabus is based on latest regulation.And the data in the csv file consists of the questions only related to the current syllabus.
There is rubrics team where they are responsible for all the constraints or criteria for example:"It should not produce same paper as last year paper".
Now we are backend team who wants to work in lean.So What backend is responsible for now we have to decide and start working
