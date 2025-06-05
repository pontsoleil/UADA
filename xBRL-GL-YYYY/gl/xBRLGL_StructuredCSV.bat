@echo off
REM Usage: .\xBRLGL_StructuredCSV.bat Customer_Invoices

set INPUT=%1
python ..\..\..\Python\xBRLGL_StructuredCSV.py ^
    -i ../OIM-CSV/XBRL-GL-2025/gl/ids/%INPUT%.xml ^
    -n 2025-12-01 ^
    -s ../XBRL-GL-2025/XBRL_GL_case-c-b-m-u-e-t-s_Structure.csv ^
    -o ../OIM-CSV/XBRL-GL-2025/gl/OIM/%INPUT%.csv ^
    -e utf-8-sig 
pause
