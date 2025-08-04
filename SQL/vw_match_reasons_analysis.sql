USE [Veridion]
GO

/****** Object:  View [dbo].[vw_match_reasons_analysis]    Script Date: 03/08/2025 05:41:43 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE VIEW [dbo].[vw_match_reasons_analysis] AS
WITH split_reasons AS (
    SELECT 
        input_row_key,
        veridion_id,
        candidate_name,
        name_similarity,
        geographic_match,
        business_context,
        overall_confidence,
        recommendation,
        match_reason,    
        LTRIM(RTRIM(value)) AS reason_component
    FROM veridion_analysis_best_matches
    CROSS APPLY STRING_SPLIT(match_reason, '|')
    WHERE match_reason IS NOT NULL 
    AND LTRIM(RTRIM(value)) != ''
),

cleaned_reasons AS (
    SELECT 
        input_row_key,
        veridion_id,
        candidate_name,
        name_similarity,
        geographic_match,
        business_context,
        overall_confidence,
        recommendation,
        match_reason,
        reason_component
    FROM split_reasons
)

SELECT 
    recommendation,
    reason_component,
    COUNT(*) as frequency,
    ROUND(
        (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY recommendation)), 2
    ) as percentage_within_recommendation,
    ROUND(
        (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2
    ) as percentage_of_total
FROM cleaned_reasons
GROUP BY recommendation, reason_component;

GO


