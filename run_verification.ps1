$log = "hezgene_test_results.log"

"=== HEZGENE AUTONOMOUS TEST SUITE ===" > $log
"Date: $(Get-Date)" >> $log
"" >> $log

"=== TEST 1: Installation ===" >> $log
hezgene --version >> $log 2>&1
"Exit code: $LASTEXITCODE" >> $log
"" >> $log

"=== TEST 2: Help System ===" >> $log
hezgene --help >> $log 2>&1
"Exit code: $LASTEXITCODE" >> $log
"" >> $log

"=== TEST 3: Status Check (No Upsells) ===" >> $log
hezgene status >> $log 2>&1
"Exit code: $LASTEXITCODE" >> $log
"" >> $log

"=== TEST 4: Config Access ===" >> $log
hezgene config --list >> $log 2>&1
"Exit code: $LASTEXITCODE" >> $log
"" >> $log

"=== TEST 5: Python Import Check ===" >> $log
python -c "from hezgene.core.engine import EvolutionEngine; print('Core OK'); from hezgene.web.app import app; print('Web OK')" >> $log 2>&1
"Exit code: $LASTEXITCODE" >> $log
"" >> $log

Write-Host "Tests complete. Check hezgene_test_results.log"
