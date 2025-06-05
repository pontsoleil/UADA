@echo off
REM Usage: .\xBRLGL_TaxonomyGenerator.bat case-c
REM -r Accntg Entrs for graphwalk LHM
REM -r AccntgEntrs for pased LHM
cd 
set INPUT=%1
python ..\..\..\Python\xBRLGL_TaxonomyGenerator.py ^
    ../OIM-CSV/XBRL-GL-2025/LHM/XBRL_GL_%INPUT%_Structure.csv ^
    -b ../OIM-CSV/XBRL-GL-2025/ ^
    -r AccntgEntrs ^
	-l ja ^
	-c usd ^
	-e utf-8-sig
pause
