// =============================================================================
//  1. L.A. CRIME RATE — POWER QUERY M SCRIPT
// =============================================================================
let
    // -------------------------------------------------------------------------
    // 2. PROMOTE HEADERS
    // -------------------------------------------------------------------------
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),

    // -------------------------------------------------------------------------
    // 3. FIX THE CORRUPTED COLUMN NAME ("FOLDING KNIFE" → weapon_description)
    // -------------------------------------------------------------------------
    RenamedWeaponColumn = Table.RenameColumns(
        PromotedHeaders,
        {{"FOLDING KNIFE", "weapon_description"}}
    ),

    // -------------------------------------------------------------------------
    // 4. SPLIT date_occurred into date + time (it currently holds "DD/MM/YYYY HH:MM")
    // -------------------------------------------------------------------------
    SplitDateOccurred = Table.SplitColumn(
        RenamedWeaponColumn,
        "date_occurred",
        Splitter.SplitTextByEachDelimiter({" "}, QuoteStyle.Csv, false),
        {"date_occurred", "time_occurred"}
    ),

    // -------------------------------------------------------------------------
    // 5. TYPE-CAST WITH UK LOCALE (en-GB) — dates are DD/MM/YYYY, NOT MM/DD/YYYY
    // -------------------------------------------------------------------------
    TypedDates = Table.TransformColumnTypes(
        SplitDateOccurred,
        {
            {"date_reported", type date},
            {"date_occurred", type date},
            {"time_occurred", type time}
        },
        "en-GB"
    ),

    // -------------------------------------------------------------------------
    // 6. TYPE-CAST NUMERIC + TEXT COLUMNS
    // -------------------------------------------------------------------------
    TypedRest = Table.TransformColumnTypes(
        TypedDates,
        {
            {"division_number", Int64.Type},
            {"area", Int64.Type},
            {"area_name", type text},
            {"reporting_district", Int64.Type},
            {"part", Int64.Type},
            {"crime_code", Int64.Type},
            {"crime_description", type text},
            {"modus_operandi", type text},
            {"victim_age", Int64.Type},
            {"victim_sex", type text},
            {"victim_descent", type text},
            {"premise_code", Int64.Type},
            {"premise_description", type text},
            {"weapon_code", Int64.Type},
            {"weapon_description", type text},
            {"status", type text},
            {"status_description", type text},
            {"location", type text},
            {"cross_street", type text},
            {"latitude", type number},
            {"longitude", type number}
        }
    ),

    // -------------------------------------------------------------------------
    // 7. CLEAN "UNKONW" (misspelled UNKNOWN) → null
    // -------------------------------------------------------------------------
    CleanWeaponText = Table.ReplaceValue(
        TypedRest,
        "UNKONW",
        null,
        Replacer.ReplaceValue,
        {"weapon_description"}
    ),

    // -------------------------------------------------------------------------
    // 8. PROPER-CASE the weapon_description for presentation
    // -------------------------------------------------------------------------
    ProperCaseWeapon = Table.TransformColumns(
        CleanWeaponText,
        {{"weapon_description", each if _ = null then null else Text.Proper(Text.Trim(_)), type nullable text}}
    ),

    // -------------------------------------------------------------------------
    // 9. REPLACE UNKNOWN-VALUE SENTINELS WITH NULL
    //    weapon_code = 0   → null    (211k+ rows)
    //    victim_age  = 0   → null    (211,842 rows)
    //    victim_sex  = "X" or empty → null
    //    victim_descent = "X" → null
    // -------------------------------------------------------------------------
    NullWeaponCode = Table.ReplaceValue(ProperCaseWeapon, 0, null, Replacer.ReplaceValue, {"weapon_code"}),
    NullVictimAge  = Table.ReplaceValue(NullWeaponCode,    0, null, Replacer.ReplaceValue, {"victim_age"}),
    NullVictimSex  = Table.ReplaceValue(NullVictimAge,
                        each [victim_sex],
                        each if [victim_sex] = "X" or [victim_sex] = "" or [victim_sex] = null then null else [victim_sex],
                        Replacer.ReplaceValue,
                        {"victim_sex"}),
    NullVictimDesc = Table.ReplaceValue(NullVictimSex,
                        each [victim_descent],
                        each if [victim_descent] = "X" or [victim_descent] = "" or [victim_descent] = null then null else [victim_descent],
                        Replacer.ReplaceValue,
                        {"victim_descent"}),

    // -------------------------------------------------------------------------
    // 10. DERIVED COLUMNS — do heavy lifting here, not in DAX (load-time, not per-visual)
    // -------------------------------------------------------------------------
    AddYear     = Table.AddColumn(NullVictimDesc, "year_occurred",     each Date.Year([date_occurred]),       Int64.Type),
    AddMonth    = Table.AddColumn(AddYear,         "month_occurred",    each Date.Month([date_occurred]),      Int64.Type),
    AddMonthName= Table.AddColumn(AddMonth,        "month_name",        each Date.MonthName([date_occurred]),  type text),
    AddQuarter  = Table.AddColumn(AddMonthName,    "quarter_occurred",  each Date.QuarterOfYear([date_occurred]), Int64.Type),
    AddWeekday  = Table.AddColumn(AddQuarter,      "weekday_name",      each Date.DayOfWeekName([date_occurred]), type text),
    AddWeekdayN = Table.AddColumn(AddWeekday,      "weekday_number",    each Date.DayOfWeek([date_occurred], Day.Monday) + 1, Int64.Type),
    AddHour     = Table.AddColumn(AddWeekdayN,     "hour_occurred",     each if [time_occurred] = null then null else Time.Hour([time_occurred]), Int64.Type),
    AddIsPart1  = Table.AddColumn(AddHour,         "is_part_1",         each [part] = 1, type logical),

    // Reporting lag (days between occurrence and report)
    AddReportLag = Table.AddColumn(
        AddIsPart1,
        "reporting_lag_days",
        each Duration.Days([date_reported] - [date_occurred]),
        Int64.Type
    ),

    // Age bands for victim demographics chart
    AddAgeBand = Table.AddColumn(
        AddReportLag,
        "victim_age_band",
        each if [victim_age] = null      then "Unknown"
        else if [victim_age] < 18        then "Under 18"
        else if [victim_age] < 25        then "18-24"
        else if [victim_age] < 35        then "25-34"
        else if [victim_age] < 50        then "35-49"
        else if [victim_age] < 65        then "50-64"
        else                                  "65+",
        type text
    ),

    // Map descent codes to human-readable labels (per LAPD codebook)
    AddDescentLabel = Table.AddColumn(
        AddAgeBand,
        "victim_descent_label",
        each
            let d = [victim_descent] in
            if d = null then "Unknown"
            else if d = "A" then "Other Asian"
            else if d = "B" then "Black"
            else if d = "C" then "Chinese"
            else if d = "D" then "Cambodian"
            else if d = "F" then "Filipino"
            else if d = "G" then "Guamanian"
            else if d = "H" then "Hispanic/Latin"
            else if d = "I" then "American Indian"
            else if d = "J" then "Japanese"
            else if d = "K" then "Korean"
            else if d = "L" then "Laotian"
            else if d = "O" then "Other"
            else if d = "P" then "Pacific Islander"
            else if d = "S" then "Samoan"
            else if d = "U" then "Hawaiian"
            else if d = "V" then "Vietnamese"
            else if d = "W" then "White"
            else if d = "Z" then "Asian Indian"
            else "Other",
        type text
    ),

    // -------------------------------------------------------------------------
    // 11. REMOVE COLUMNS THAT ARE MOSTLY NULL / NOT USED IN VISUALS
    //     crime_code_2..4 and cross_street are >95% null per validation pass.
    // -------------------------------------------------------------------------
    RemovedColumns = Table.RemoveColumns(
        AddDescentLabel,
        {"crime_code_2", "crime_code_3", "crime_code_4", "cross_street"},
        MissingField.Ignore
    )
in
    RemovedColumns
