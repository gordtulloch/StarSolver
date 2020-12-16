#!/bin/bash

if [ -f 'app/.installed' ]; then
   if [ -f 'app/solver.py' ]; then
      source app/.venv/bin/activate
      python app/solver.py $1
   else
      echo "Cannot find Starseeker (no solver.py in app directory?)"
      exit 1
   fi
   deactivate
   exit 0
fi


echo Welcome to the Starseeker install script
echo -n Checking for python ...

# check that we have python ...
if command -v python &> /dev/null
then
#if [ $? -eq 0 ]; then
   echo found
else
   echo No python found
   echo You need to install python from python.org
   echo Please choose version 3.7.9
   exit 1
fi

# ... and pip
echo -n Checking for pip ...
if command -v pip &> /dev/null
then
#if [ $? -eq 0 ]; then
   echo found
else
   echo not found. 
   echo You need to install pip
   exit 1
fi

# check we have requirements.txt
echo -n Checking for requirements.txt ...
if [ -f "app/requirements.txt" ]; then
	echo found
else
	echo not found
	echo You should have a requirements.txt in this directory
	exit 1
fi

if [ -d "app/.venv" ]; then
   echo "Virtual environment already made; skipping"
else
   # install in virtual environment
   echo -n Setting up virtual environment...
   python -m venv app/.venv
   if [ $? -eq 0 ]; then
      echo done
   else
      echo failed
      exit 1
   fi
fi

echo -n Activating virtual environment ...
source app/.venv/bin/activate
if [ $? -eq 0 ]; then
   echo done
else
   echo failed to activate
   exit 1
fi

echo -n Installing dependencies ...
# pip install -r app/requirements.txt
pip  install -r app/requirements.txt --no-cache-dir
if [ $? -eq 0 ]; then
   echo done
else
   echo Install failed
   exit 1
fi

#echo Creating user data directories ...
#mkdir watched snapshots deleted calibration catalogues exports &> /dev/null

touch app/.installed

if [ -f 'app/solver.py' ]; then
   echo
   echo 'Starseeker installed successfully -----------------------------'
   echo
   echo "Running Starseeker. This will be slow the first time while"
   echo "compilation takes place but will be a lot faster"
   echo "on subsequent runs. Type the same command to run next time"
   echo
   echo "  ./starseeker"
   echo
   echo "In case of any issues, run Starseeker in debug mode"
   echo
   echo "  ./starseeker debug"
   echo
   echo "then send the output by PM to me, Martin Meredith @ SGL "
   echo "and I will be happy to help."
   echo
   echo "I hope you enjoy using Starseeker. Don't forget to read"
   echo "the manual :-)"
   echo
   echo '------------------------------------------------------------'
   python app/solver.py
else
   echo "Cannot find Starseeker (no solver.py in current directory?)"
   exit 1
fi
exit 0


# echo "starting Starseeker"
# python solver.py debug

