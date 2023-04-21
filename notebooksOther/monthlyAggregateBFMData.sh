#!/bin/bash
#SBATCH --account=uBOC2_mentasc
#SBATCH --partition=g100_all_serial
##SBATCH --partition=g100_usr_prod
##SBATCH --qos=noQOS
#SBATCH --mem=30G
#SBATCH --nodes 1
#SBATCH --ntasks-per-node=1
#SBATCH --time=4:00:00
#SBATCH --job-name=monthlyAggregateBFMData
#SBATCH --output=monthlyAggregateBFMData_%j.out
#SBATCH --error=monthlyAggregateBFMData_%j.err
#SBATCH --mail-user=lorenzo.mentaschi@unibo.it

py=/g100/home/userexternal/lmentasc/usr/Miniconda3/bin/python3.9

rm BFM_1monclim* BFM_monthly*
$py monthlyAggregateBFMData.py
