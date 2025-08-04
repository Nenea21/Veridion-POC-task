USE [Veridion]
GO

/****** Object:  View [dbo].[vw_detailed_match_reasons]    Script Date: 03/08/2025 05:40:55 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



CREATE VIEW [dbo].[vw_detailed_match_reasons] AS
SELECT 
    recommendation,
    match_reason,
    COUNT(*) as count_occurrences,
    ROUND(
        (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY recommendation)), 2
    ) as percentage_within_recommendation,
    ROUND(
        (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2
    ) as percentage_of_total
FROM veridion_analysis_best_matches
WHERE match_reason IS NOT NULL
GROUP BY recommendation, match_reason;

GO


