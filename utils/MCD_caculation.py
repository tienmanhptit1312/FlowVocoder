import json
import os

import numpy as np 
import argparse
import multiprocessing as mp 
import sys

from fastdtw import fastdtw
from glob import glob
# from preprocessing import WORLD_processing
import librosa
from WORLD_processing import *
import scipy.spatial


def get_feature(wav, fs=16000):
    f0, timeaxis, sp, ap, mc = world_encode_data(wav, fs)
    return f0, mc

def evaluate_mcd(source_spk, target_spk, file_path1, file_path2):

    MCD_array = []
    utt_list = [utt for utt in os.listdir(os.path.join(file_path2, source_spk))]
    print('utt list: ', utt_list)
    print('sorted utt list: ', sorted(utt_list))
    for utt in utt_list:
        utt_id = utt.split('.')[0]
        # read source features , target features and converted mcc
        src_data = np.load(os.path.join(file_path2, source_spk, utt))
        trg_data = np.load(os.path.join(file_path1, target_spk, utt))

        # non-silence parts
        trg_idx = np.where(trg_data['f0']>0)[0]
        trg_mcc = trg_data['mcc'][trg_idx,:24]
        # print('trg_mcc shape: ', trg_mcc.shape)
        src_idx = np.where(src_data['f0']>0)[0]
        src_mcc = src_data['mcc'][src_idx,:24]

        # DTW
        _, path = fastdtw(src_mcc, trg_mcc, dist=scipy.spatial.distance.euclidean)
        twf = np.array(path).T
        cvt_mcc_dtw = src_mcc[twf[0]]
        trg_mcc_dtw = trg_mcc[twf[1]]

        # MCD 
        diff2sum = np.sum((cvt_mcc_dtw - trg_mcc_dtw)**2, 1)
        mcd = np.mean(10.0 / np.log(10.0) * np.sqrt(2 * diff2sum), 0)
        # logging.info('{} {}'.format(basename, mcd))
        print('utterance {} mcd: {}'.format(utt_id, mcd))
        MCD_array.append(mcd)

    return MCD_array

def evaluate_mcd_wav(source_spk, target_spk, src_filepath, trg_filepath):
    """ 
    file_path2: conversion file dir 
    file_path1: source file dir
    """

    MCD_array = []
    # utt_list = [utt for utt in os.listdir(os.path.join(file_path2, "cvt_"+source_spk+"_"+target_spk))]
    utt_list = glob(os.path.join(trg_filepath, "*.wav"))

    print('utt list: ', utt_list)
    print('sorted utt list: ', sorted(utt_list))
    for utt in utt_list:
        
        utt_name = utt.split("/")[-1]
        src_data,_ = librosa.load(os.path.join(src_filepath, utt_name), sr=22050)
        trg_data,_ = librosa.load(utt, sr=22050)

        src_f0, src_mcc = get_feature(src_data)
        trg_f0, trg_mcc = get_feature(trg_data)

        # non-silence parts
        trg_idx = np.where(trg_f0>0)[0]
        # print('trg idx: ', trg_idx)
        trg_mcc = trg_mcc[trg_idx,:24]
        # print('trg_mcc shape: ', trg_mcc.shape)
        src_idx = np.where(src_f0>0)[0]
        src_mcc = src_mcc[src_idx,:24]

        # DTW
        _, path = fastdtw(src_mcc, trg_mcc, dist=scipy.spatial.distance.euclidean)
        twf = np.array(path).T
        cvt_mcc_dtw = src_mcc[twf[0]]
        trg_mcc_dtw = trg_mcc[twf[1]]

        # MCD 
        diff2sum = np.sum((cvt_mcc_dtw - trg_mcc_dtw)**2, 1)
        mcd = np.mean(10.0 / np.log(10.0) * np.sqrt(2 * diff2sum), 0)
        print('utterance {} mcd: {}'.format(utt_name, mcd))
        MCD_array.append(mcd)

    return MCD_array


if __name__ =='__main__':
    
    source_spk = 'ground-truth'
    # source_spk = 'VCC2SF1'
    target_spk = 'flowvocoder'
    root_dir = "../Neural-Vocoder-Experiment"
    src_filepath = os.path.join(root_dir, source_spk)
    
    trg_filepath = os.path.join(root_dir, target_spk)
    print(trg_filepath)

    MCD_arr = evaluate_mcd_wav(source_spk, target_spk, src_filepath, trg_filepath)

    mcd_value = np.mean(np.array(MCD_arr))

    print('MCD value between two speaker: ', mcd_value)
