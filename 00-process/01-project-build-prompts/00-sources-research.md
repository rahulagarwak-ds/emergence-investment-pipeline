# Sources Research : Prompt 1

## Role

You are a top notch market researcher and analyst working for our partners in a seed stage VC firm

## Purpose

To research and select top 1 freely available platforms(below) based on metrics and data available for potential startups
Platforms must be freely accesible/public, information must be as fresh as possible, quality of the information needs to defensible, citable, consistent

We also must identify a source of freshesss or traction signal such as github activity, funding news, recent launch information to be included in the final metrics/information signals

Constraint: The platform must be freely accessible or public 

## Primary Platforms
    
    - Product Hunt
    - YC
    - Hacker News
    - Twitter/X
    - Crunchbase

## Task

    - Research the platforms given and go through 4-5 startup candidates per platform where available
    - analyse all available data and metrics
    - generalize the pattern of the data available
    - standardize the data into segments and key metrics or information that will be valuable for a partner to know and decide to invest their time on the startup
    - rank each platform based on the importance of the available data as well as coverage of each data point and metrics
    - each metric number need to give us unique information if two or metrics are giving us same or correlated values they need to be used as proxies to be used when primary is null/empty
    - textual information must be used to infer something meaningful and proxy rule will apply to textual fields as well
    - we need at least one signal that will convey freshness or traction for the picked startup candidate
    - use the two dimensions
        - Quality: how useful, unique, reliable, and decision-relevant the signal is
        - Coverage: how consistently the signal is available across sampled startups
    - use binary scoring or 1-10 scale to make a defensible decision the unique and standardized list of metrics/information to be considered for next steps: which would be the analysis of the startups against the thesis
    - correlated metrics should not doouble count the score but used as a fallback only

## Output

    - create a document 00-source-selection-primary.md inside 00-process/_intermediate-files-outputs folder
    - use minimum verbosity
    - use top down approach with the decisions at the top and then drill down into why the decision was made
        - Selected source
        - Why they were chosen
        - platform comparison 
        - singal set(standardized)
        - rules for proxy if any
        - limitations/assumptions
    - for each selected source list down the information/metrics we need to use
    - mark most consistent freshness signal as a standalone separate metrics

Context source: _resources/case-study-problem-statement.md

# Sources Research : Prompt 2

Use Prompt 1 above as context and execute below

do a dry run for input text such as "AI agents for SMBs" or a feed like the "YC W25 batch" and check the information available to ensure we can get the details as listed in 00-process/_intermediate-files-outputs/00-source-selection-primary.md

remember this is a completeness check

your output will be 00-process/_intermediate-files-outputs/01-source-selection-dry-run.md
I need a summary of covered metrics and a 1-10 score of the quality and coverage

# Sources Research : Prompt 3

Use prompt 1 and 2 for context
and use HN as a source and compre the exact same inputs as done for prompt 2 for YC

remember this is a cross reference completeness check
your output will be 00-process/_intermediate-files-outputs/02-source-selection-dry-run-alternative.md
I need a summary of covered metrics and a 1-10 score of the quality and coverage and a quick comparison from the results in 00-process/02-project-key-decisions/01-source-selection-dry-run.md

# Sources Research : Prompt 4

We already have a backup of the current 00-process/03-project-documents/00-source-selection.md document but i noticed in architecture we have a mention of HN as an optional source
I want the source selection document to be modified to authoratatively say the final selected source(the winner of the source selection) so downstream work can have a clear picture
no content changes on one section addition as a source selection clear winner