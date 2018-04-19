# Continuous Evaluation

## Problem Settings

Developers of an AI system want to see their efforts are improving the effectiveness of their work. For example, if we are developing an image classification system, we would like to see that with the merge of more and more pull requests, the system could have higher precision and higher recall values.  From this example, we see the following concepts:

1. An AI system has several KPIs.  The image classification system has two KPIs -- precision and recall.
1. KPIs are supposed to be improved (increment or decrement) with respect to Git commits.

## The Solution as a Table

We propose to develop a tool, the *Continuous Evaluation* program, which checks out each Git commits (or, for saving the computational resource, only Git merge commits on the main branch), builds and runs the *KPI evaluation programs* in the commit.  

A KPI evaluation program is the one that computes and prints one or more KPIs.

Given that each Git commit is immutable and has a timestamp, and each Git commit contains some KPI evaluation programs that prints a number, say, N, KPI values, the running of the continuous evaluation program with the AI system's Git repository should fill a table with the following scheme:

| Git commit SHA | Date & Time | KPI 1 (precision) | KPI 2 (recall) |
|----------------|-------------|-------------------|----------------|
| 195aef12       | 2018-01-01  | 50.01%            | 49.17%         |
| 4u059674       | 2018-01-02  | 51.01%            | 55.41%         |
| 39bcc9e1       | 2018-01-03  | 29.01%            | 78.17%         |
| 867abbce       | 2018-01-04  | 58.01%            | 40.92%         |

Here we noticed that the precision generally keeps growing, but the number 29.01% on 2018-01-03 is a decrease, thus warns us about something wrong with the merge commit 39bcc9e1 and reminds us to check the corresponding pull request.

## Fills in the Table

KPI programs in the repository to be evaluated continuously takes the responsibility to compute the KPI values. It doesn't add much letting KPI programs to write the values to storage, e.g., [Google Sheets](https://developers.google.com/sheets/guides/concepts). Comparing to alternatives that require a third-party to collect KPIs and write them into the storage, it is simpler to rely on KPI programs to write. 

In order to fill in a Google Sheets, KPI programs need 

1. the access token of Google Sheets API,
1. the Git repository URL, as the table (sheet) name, and
1. the (current) Git commit, as the row ID.

The KPI programs do not have the above information, but they could get them from environment variables:

1. CONTINUOUS_EVALUATION_GOOGLE_SHEETS_TOEKN
1. CONTINUOUS_EVALUATION_SHEET_NAME
1. CONTINUOUS_EVALUATION_ROW_ID

## KPI Programs and Unit Tests

Please be aware that the KPI programs could be unit tests.  If so, we can use CI systems to trigger the running of KPI programs.  We might not want to run KPI programs for all pull requests commits because it might take too long time to run each KPI, and need unit tests to check if they should run the KPIs.

```c++
TEST(ImageClassification, PrecisionKPI) {
  char* token = std::getenv("CONTINUOUS_EVALUATION_GOOGLE_SHEETS_TOEKN");
  char* sheet = std::getenv("CONTINUOUS_EVALUATION_SHEET_NAME");
  char* row = std::getenv("CONTINUOUS_EVALUATION_ROW_ID");

  if (token != nullptr && sheet != nullptr && row != nullptr) {
     double precision = ComputePrecision();
     google_sheets.v4.WriteCell(token, sheet, row, "KPI 1 (Precision)", precision);
  }
}
```

## Evaluate A Certain Commit

If we have sufficient CI servers and want to run KPIs before we merge Pulls, we can configure the CI systems (e.g., TeamCity) to activate the KPI unit tests by setting the values of `CONTINUOUS_EVALUATION_GOOGLE_SHEETS_TOEKN`, `CONTINUOUS_EVALUATION_SHEET_NAME`, and `CONTINUOUS_EVALUATION_ROW_ID`. 

This also ensures that the above sensitive information resides on CI system other than in our source code, which is publicly available.

## Evaluate Many Commits

If we want to run KPIs of some selected commits, e.g., all merge commits in the `develop` branch, we can do the following:

1. Select these commits from Git, for example,
 
   ```bash
   git checkout develop
   git log --merges
   ```
   
1. Dump the above output into a CSV file and import to Google Sheets.  The schema of the CSV file should include a **build status** flag, whose value could be 

   - "TODO": the commit hasn't been built, and the KPI programs were not running
   - "DOING": some program is building and running the commit
   - "FAILED": some program has built and run the commit, but it somehow failed. The log could be in an additional column **build log**,
   - "SUCCESS": the commit was built and ran, and all KPIs were recorded.
   
   The updated schema is as follows:
   
   | Git commit SHA | Date & Time | KPI 1 (Precision) | KPI 2 (Recall) | Build Status | Build Log |
   |----------------|-------------|-------|------|--------------|-----------|
   
1. Write a Bash program, that calls Google Sheet command line tool, to checkout the Git commits whose build status is "TODO", and build and run.

   - If given a command line flag `--retry-failed`, this program also try to build and run those with build status is "FAILED".
   - **We can run as many instances of this program on all available computers to complete all selected commits as soon as possible**.
   - **We can add/delete commits in the Google Sheet when the above program is running.**

## Analyses the stability of a model

Before add a new model to the baseline. We must ensure that the kpi data has a little change in each running. In this way, we can say the Continuous Evaluation System is workable.

When you want to check the stability of a model, you can use the following file:
- `run.xsh` , a script to check the stability of given model.

It need two parameter：
- `--task_dir` , the model  dir name you want to check，it should be in the tasks dir of CE framework.
- `--times` , the times you want to run the model.

This is a example：
```bash
./run.xsh --task_dir=resnet50 --times=10
```
