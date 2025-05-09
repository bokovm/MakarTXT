@echo off
cd C:\Programming\serverTxt

git add .
git commit -m "Auto %date% %time%"
git push origin master
pause