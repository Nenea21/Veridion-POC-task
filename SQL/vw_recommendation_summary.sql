USE [Veridion]
GO

/****** Object:  View [dbo].[vw_recommendation_summary]    Script Date: 03/08/2025 05:42:22 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE VIEW [dbo].[vw_recommendation_summary] AS
WITH split_reasons AS (
    SELECT 
        input_row_key,
        overall_confidence,
        recommendation
    FROM veridion_analysis_best_matches
    CROSS APPLY STRING_SPLIT(match_reason, '|')
    WHERE match_reason IS NOT NULL 
    AND LTRIM(RTRIM(value)) != ''
),

summary_stats AS (
    SELECT 
        recommendation,
        COUNT(DISTINCT input_row_key) as total_records,
        ROUND(AVG(overall_confidence), 2) as avg_confidence,
        MIN(overall_confidence) as min_confidence,
        MAX(overall_confidence) as max_confidence
    FROM split_reasons
    GROUP BY recommendation
),

grand_total AS (
    SELECT COUNT(DISTINCT input_row_key) as total_count
    FROM split_reasons
)

SELECT 
    s.recommendation,
    s.total_records,
    ROUND((s.total_records * 100.0 / g.total_count), 2) as percentage_of_total,
    s.avg_confidence,
    s.min_confidence,
    s.max_confidence
FROM summary_stats s
CROSS JOIN grand_total g;

GO


