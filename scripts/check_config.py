#! /usr/bin/env python
########################################################################
#
# Name: check_config.py
#
# Purpose: Make configuration checks on a file or group of files.
#
# Usage:
#
# check_config.py [options]
#
# Options:
#
# -h|--help            - Print help message.
# -f|--file <path>     - Specify file to check (full path, repeatable).
# -d|--dir <dir>       - Check all .root files in specified directory (repeatable).
# -c|--config <fcl>    - Check fcl file.
#
# The following options control variations (only for fcl mode).
#
# --trigger <trigger>  - Specify hardware trigger (bnb, numi, ext).
# --beam <beam>        - Specify beam type (bnb, numi).
# --epoch <epoch>      - Specify epoch (1x, 2x, 3x, 4x, 5).
# --overlay            - Specify overlay.
#
# The following options control which checks are performed.
# If none of these options is specified, all checks are performed.
# Otherwise, just the specified checks are performed.
# Use "--no-" prefix to skip specified checks.
#
# --[no-]crt                - Check CRT (artroot mode only).
# --[no-]services           - Check services.
# --[no-]output             - Check RootOutput.
# --[no-]timing             - Check beam timing.
# --[no-]optical            - Check optical waveform selection.
# --[no-]flux               - Check flux.
# --[no-]remap              - Check PMT remapping.
#
########################################################################
#
# Created: 24-Jun-2025  H. Greenlee
#
# Usage notes.
#
# 1.  Invoking this script without any options is equivalent to invoking
#     with option "--dir ." (i.e. check root files in current directory).
#
# 2.  Fcl configurations can be checked by fcl files or artroot files.
#     When checking artroot files, fcl configurations are extracted automatically
#     from the processing history or sam metadata.
#
# 3.  To fully check a fcl configuration, it is necessary to specify the following
#     parameters.
#
#     a) Hardware trigger (bnb, numi, ext).
#     b) Beam type (bnb, numi).
#     c) Epoch (1x, 2x, 3x, 4x, 5).
#     d) Overlay flag.
#
#     Beam timing is fully specified by the combination of hardware trigger
#     and beam type.
#
#     The beam type corresponds to either of the following:
#
#     a) The software trigger stream (for real data).
#     b) The simulated beam gate (for mc or overlay).
#
#     The hardware trigger type is the actual or simulated hardware trigger.
#     For beam on data, it is "bnb" or "numi."  For beam off data or overlay,
#     it should be "ext."
#
# 4.  When checking artroot files, trigger, beam, epoch, and overlay arguments
#     are ignored.  They are determined from file itself.
#
########################################################################

from __future__ import print_function
import sys, os, random, subprocess, io
import larbatch_utilities
import fcl
import check_crt_merge
import samweb_cli

# Import ROOT module.
# Globally turn off root warning and error messages.
# Don't let root see our command line options.

myargv = sys.argv
sys.argv = myargv[0:1]
if 'TERM' in os.environ:
    del os.environ['TERM']
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kFatal
sys.argv = myargv


# Global variables.

samweb = samweb_cli.SAMWebClient(experiment = 'uboone')
artroot_files = set()        # Files that are known to be artroot.
non_artroot_files = set()    # Files that are known to not be artroot.

# Help function.

def help():

    filename = sys.argv[0]
    file = open(filename, 'r')

    doprint=0
    
    for line in file.readlines():
        if line[2:].startswith('check_config.py'):
            doprint = 1
        elif line.startswith('######') and doprint:
            doprint = 0
        if doprint:
            if len(line) > 2:
                print(line[2:], end='')
            else:
                print()


# Determine epoch from metadata dictionary.

def get_epoch(md):

    runs = set()
    epochs = set()

    # Extract run number.

    if 'runs' in md:
        mdruns = md['runs']
        for mdrun in mdruns:
            run = mdrun[0]
            runs.add(run)

    for run in runs:

        # Determine epoch (1a-5) for this run.

        epoch = ''
        if run > 25769:
            epoch = '6'
        elif run > 24319:
            epoch = '5'
        elif run > 22269:
            epoch = '4d'
        elif run > 21285:
            epoch = '4c'
        elif run > 19752:
            epoch = '4b'
        elif run > 18960:
            epoch = '4a'
        elif run > 14116:
            epoch = '3b'
        elif run > 13696:
            epoch = '3a'
        elif run > 11048:
            epoch = '2b'
        elif run > 8316:
            epoch = '2a'
        elif run > 4951:
            epoch = '1c'
        elif run > 3984:
            epoch = '1b'
        elif run > 3419:
            epoch = '1a'
        else:
            epoch = '0'

        if not epoch in epochs:
            epochs.add(epoch)

    epoch = ''
    if len(epochs) == 1:
        epoch = epochs.pop()
    else:
        print('File has more than one epoch.')

    # Done.

    return epoch


# Check beam timing.  Return True of OK.

def check_beam_timing(cfg, trigbit, beam):

    result = True

    # Calculate nominal beam gate times.

    beam_start = 0.
    beam_end = 0.

    # Common optical filter timing.

    beam_start_tick = 0.
    beam_end_tick = 0.
    veto_start_tick = 0.
    veto_end_tick = 0.

    if trigbit == 11 and beam == 'bnb':
        beam_start = 3.195
        beam_end = 4.875
        beam_start_tick = 190
        beam_end_tick = 320
        veto_start_tick = 60
        veto_end_tick = 190
    elif trigbit == 12 and beam == 'numi':
        beam_start = 5.64
        beam_end = 15.44
        beam_start_tick = 300
        beam_end_tick = 1050
        veto_start_tick = 170
        veto_end_tick = 300
    elif trigbit == 9 and beam == 'bnb':
        beam_start = 3.57
        beam_end = 5.25
        beam_start_tick = 214
        beam_end_tick = 344
        veto_start_tick = 84
        veto_end_tick = 214
    elif trigbit == 9 and beam == 'numi':
        beam_start = 6.00
        beam_end = 15.80
        beam_start_tick = 323
        beam_end_tick = 1073
        veto_start_tick = 193
        veto_end_tick = 323
    else:
        print('Unknown beam timing configuration.')
        sys.exit(1)

    # Scan fcl parameters again to check beam timings.

    print()
    print('Checking beam timings.')
    print('Nominal beam gate start = %8.3f, end = %8.3f' % (beam_start, beam_end))
    print('Common optical filter gate start = %d, end = %d' % (beam_start_tick, beam_end_tick))
    print('Common optical filter veto start = %d, end = %d' % (veto_start_tick, veto_end_tick))
    print()

    # Loop over procsss names.

    for process_name in cfg:

        # Ignore any processes run in swizzler.

        if process_name == 'Swizzler':
            continue

        # Ignore any processes run in reco1 except stand alone optical reco.

        if process_name.find('Stage1') >= 0 and not process_name.endswith('Optical'):
            continue

        print('Checking process name %s' % process_name)
        fcl_proc = cfg[process_name]

        if 'physics' in fcl_proc:
            fcl_physics = fcl_proc['physics']

            # Extract lists of module by type.

            producers = {}
            filters = {}
            analyzers = {}
            outputs = {}

            if 'producers' in fcl_physics:
                producers = fcl_physics['producers']
            if 'filters' in fcl_physics:
                filters = fcl_physics['filters']
            if 'analyzers' in fcl_physics:
                analyzers = fcl_physics['analyzers']
            if 'outputs' in fcl_proc:
                outputs = fcl_proc['outputs']

            # Loop over modules in trigger paths.

            if 'trigger_paths' in fcl_physics:
                trigger_paths = fcl_physics['trigger_paths']

                # Loop over trigger path modules.

                for trigger_path in trigger_paths:
                    if trigger_path in fcl_physics:
                        modules = fcl_physics[trigger_path]
                        for module in modules:
                            if not module in producers and not module in filters:
                                print('  ***** Module %s not found.' % module)
                                result = False
                            elif module in producers:
                                module_type = producers[module]['module_type']

                                if module_type == 'StoreFlashMatchChi2':

                                    print('\n  ===== Checking flash match timing.')
                                    t1 = producers[module]['BeamWindowStart']
                                    t2 = producers[module]['BeamWindowEnd']
                                    print('  Flash match beam start = %8.3f, end = %8.3f' % (t1, t2))
                                    if abs(beam_start - t1) > 0.01 or abs(beam_end -t2) > 0.01:
                                        print('  ***** Beam timing mismatch.')
                                        result = False
                                    else:
                                        print('  Timing OK.')
                                    print()

                                elif module_type == 'LArPandoraExternalEventBuilding':

                                    if 'SliceIdTool' in producers[module]:
                                        slice_id_tool = producers[module]['SliceIdTool']
                                        if slice_id_tool['tool_type'] == 'FlashNeutrinoId':

                                            print('\n  ===== Checking Slice Id tool beam timing.')
                                            t1 = slice_id_tool['BeamWindowStartTime']
                                            t2 = slice_id_tool['BeamWindowEndTime']
                                            print('  Slice id beam start    = %8.3f, end = %8.3f' % (t1, t2))
                                            if abs(beam_start - t1) > 0.01 or abs(beam_end -t2) > 0.01:
                                                print('  ***** Slice id timing mismatch.')
                                                result = False
                                            else:
                                                print('  Timing OK.')
                                            print()

                            elif module in filters:
                                module_type = filters[module]['module_type']

                                if module_type == 'UBCRTCosmicFilter':

                                    print('\n  ===== Checking UBCRTCosmicFilter timing.')
                                    t1 = filters[module]['BeamStart']
                                    t2 = filters[module]['BeamEnd']
                                    print('  Cosmic veto beam start = %8.3f, end = %8.3f' % (t1, t2))
                                    if abs(beam_start - t1) > 0.01 or abs(beam_end -t2) > 0.01:
                                        print('  ***** Cosmic veto timing mismatch.')
                                        result = False
                                    else:
                                        print('  Timing OK.')
                                    print()

                                elif module_type == 'DLPMTPreCuts':

                                    # Ignore wrong trigger module in swizzler.

                                    if process_name == 'Swizzler':
                                        if trigbit == 11 and module == 'opfiltercommonext':
                                            continue
                                        if trigbit == 9 and module == 'opfiltercommonbnb':
                                            continue                                            

                                    print('\n  ===== Checking DLPMTPreCuts.')
                                    inp = filters[module]['OpHitProducer']
                                    print('  Optical filter producer = %s' % inp)
                                    if inp != 'ophitBeam':
                                       print('  ***** Wrong producer.')
                                       result = False
                                    else:
                                        print('  Producer OK.')
                                    t1b = filters[module]['WinStartTick']
                                    t2b = filters[module]['WinEndTick']
                                    t1v = filters[module]['VetoStartTick']
                                    t2v = filters[module]['VetoEndTick']
                                    print('  Optical filter beam start = %d, beam end = %d' % (t1b, t2b))
                                    print('  Optical filter veto start = %d, veto end = %d' % (t1v, t2v))
                                    if beam_start_tick != t1b or beam_end_tick != t2b or \
                                       veto_start_tick != t1v or veto_end_tick != t2v:
                                        print('  ***** Optical filter timing mismatch.')
                                        result = False
                                    else:
                                        print('  Timing OK.')
                                    print()
    # Done.

    print()
    print ('Done checking beam timing.')
    if result:
        print('Beam timing OK.')
    else:
        print('Beam timing bad.')
    return result


# Check optical waveform selection.

def check_optical(cfg, trigbit, beam, epoch, is_overlay):

    result = True

    # Calculate nominal high gain beam waveform.

    hgbeam = ''
    hgbeamwc = ''
    hgcosmic = ''
    if is_overlay:
        hgbeam = 'mixer'
        hgbeamwc = 'mixer'
        hgcosmic = 'pmtreadout'
    else:
        if epoch >= '4' and trigbit == 11 and beam == 'bnb':
            hgbeam = 'doublePMTFilter'
            hgbeamwc = 'pmtreadout'
            hgcosmic = 'pmtreadout'
        elif (epoch == '1a' or epoch == '1b'):
            hgbeam = 'doublePMTFilter'
            hgbeamwc = 'doublePMTFilter'
            hgcosmic = 'cosmicPMTFilter'
        else:
            hgbeam = 'pmtreadout'
            hgbeamwc = 'pmtreadout'
            hgcosmic = 'pmtreadout'

    print()
    print('Checking optical reconstruction.')
    print('High Gain beam waveform label should be "%s".' % hgbeam)
    print('WC High Gain beam waveform label should be "%s".' % hgbeamwc)
    print('High Gain cosmic waveform label should be "%s".' % hgcosmic)
    print()

    # Loop over processes.

    for process_name in cfg:

        # Ignore any processes run in swizzler or reco1.

        if process_name == 'Swizzler':
            continue

        # Ignore any processes run in reco1 except stand alone optical reco.

        if process_name.find('Stage1') >= 0 and not process_name.endswith('Optical'):
            continue

        print('Checking process name %s' % process_name)
        fcl_proc = cfg[process_name]

        if 'physics' in fcl_proc:
            fcl_physics = fcl_proc['physics']

            # Extract lists of module by type.

            producers = {}
            filters = {}
            analyzers = {}
            outputs = {}
            if 'producers' in fcl_physics:
                producers = fcl_physics['producers']
            if 'filters' in fcl_physics:
                filters = fcl_physics['filters']
            if 'analyzers' in fcl_physics:
                analyzers = fcl_physics['analyzers']
            if 'outputs' in fcl_proc:
                outputs = fcl_proc['outputs']

            # Loop over modules in trigger paths.

            if 'trigger_paths' in fcl_physics:
                trigger_paths = fcl_physics['trigger_paths']

                # Loop over trigger path modules.

                for trigger_path in trigger_paths:
                    if trigger_path in fcl_physics:
                        modules = fcl_physics[trigger_path]
                        for module in modules:
                            if not module in producers and not module in filters:
                                print('  ***** Module %s not found.' % module)
                                result = False
                            elif module in producers:
                                module_type = producers[module]['module_type']
                                if module_type == 'OpDigitSaturationCorrection':

                                    # Saturation module.

                                    print('\n  ===== Checking saturation module.')
                                    label1 = producers[module]['HGProducer']
                                    label2 = producers[module]['HGProducerCosmic']
                                    print('  HG Beam = %s' % label1)
                                    print('  HG Cosmic = %s' % label2)

                                    # We don't consider it an error if the expected
                                    # waveform is pmtreadout, but the actual waveform
                                    # is doublePMTFilter or cosmicPMTFilter.

                                    if (label1 != hgbeam and (is_overlay or label1 != 'doublePMTFilter')) or \
                                       (label2 != hgcosmic and (is_overlay or label2 != 'cosmicPMTFilter')):
                                        print('  ***** Wrong waveform label.')
                                        result = False
                                    else:
                                        print('  Waveform label OK.')
                                    print()

                                elif module_type == 'UBWCFlashFinder':

                                    # WCopflash

                                    print('\n  ===== Checking wcopflash module.')
                                    label1 = producers[module]['OpDataProducerBeam']
                                    label2 = producers[module]['OpDataProducerCosmic']
                                    print('  HG Beam = %s' % label1)
                                    print('  HG Cosmic = %s' % label2)

                                    if (label1 != hgbeamwc and (is_overlay or label1 != 'doublePMTFilter')) or \
                                       (label2 != hgcosmic and (is_overlay or label2 != 'cosmicPMTFilter')):
                                        print('  ***** Wrong waveform label.')
                                        result = False
                                    else:
                                        print('  Waveform label OK.')
                                    print()

                                elif module_type == 'ACPTtrig' and not is_overlay:

                                    # ACPTtrig

                                    print('\n  ===== Checking ACPTtrig module.')
                                    label1 = producers[module]['OpDetWfmProducer']
                                    n = label1.find(':')
                                    if n >= 0:
                                        label1 = label1[:n]
                                    print('  HG Beam = %s' % label1)
                                    if label1 != hgbeam and (is_overlay or label1 != 'doublePMTFilter'):
                                        print('  ***** Wrong waveform label.')
                                        result = False
                                    else:
                                        print('  Waveform label OK.')
                                    print()

                            elif module in filters:

                                module_type = filters[module]['module_type']
                                if module_type == 'NeutrinoSelectionFilter':

                                    print('\n  ===== Checking NeutrinoSelectionFilter.')
                                    timing_tool = filters[module]['AnalysisTools']['timing']
                                    label1 = 'pmtreadout:OpdetBeamHighGain'
                                    if 'nstimePMTWFproducer' in timing_tool:
                                        label1 = timing_tool['nstimePMTWFproducer']
                                    n = label1.find(':')
                                    if n >= 0:
                                        label1 = label1[:n]
                                    print('  HG Beam = %s' % label1)
                                    if label1 != hgbeam and (is_overlay or label1 != 'doublePMTFilter'):
                                        print('  ***** Wrong waveform label.')
                                        result = False
                                    else:
                                        print('  Waveform label OK.')
                                    print()
                                
                                


            # Loop over modules in end paths.

            if 'end_paths' in fcl_physics:
                end_paths = fcl_physics['end_paths']

                # Loop over end path modules.

                for end_path in end_paths:
                    if end_path in fcl_physics:
                        modules = fcl_physics[end_path]
                        for module in modules:
                            if not module in analyzers and not module in outputs:
                                print('  ***** Module %s not found.' % module)
                                result = False

                            elif module in analyzers:

                                module_type = analyzers[module]['module_type']
                                if module_type == 'CellTreeUB':

                                    # CellTreeUB analyzer (part of reco2).

                                    print('\n  ===== Checking CellTreeUB module.')
                                    label1 = ''
                                    if is_overlay:                                        
                                        label1 = analyzers[module]['PMT_overlay_mixer_producer']
                                    else:
                                        label1 = analyzers[module]['PMT_HG_beamProducer']
                                    label2 = analyzers[module]['PMT_HG_cosmicProducer']
                                    print('  HG Beam = %s' % label1)
                                    print('  HG Cosmic = %s' % label2)
                                    if (label1 != hgbeamwc and (is_overlay or label1 != 'doublePMTFilter')) or \
                                       (label2 != hgcosmic and (is_overlay or label2 != 'cosmicPMTFilter')):
                                        print('  ***** Wrong waveform label.')
                                        result = False
                                    else:
                                        print('  Waveform label OK.')
                                    print()

                                if module_type == 'WireCellAnaTree':

                                    print('\n  ===== Checking WireCellAnaTree.')
                                    label1 = 'pmtreadout:OpdetBeamHighGain'
                                    if 'nstimePMTLabel' in analyzers[module]:
                                        label1 = analyzers[module]['nstimePMTLabel']
                                    n = label1.find(':')
                                    if n >= 0:
                                        label1 = label1[:n]
                                    print('  HG Beam = %s' % label1)
                                    if label1 != hgbeamwc and (is_overlay or label1 != 'doublePMTFilter'):
                                        print('  ***** Wrong waveform label.')
                                        result = False
                                    else:
                                        print('  Waveform label OK.')
                                    print()


    # Done.

    print()
    print('Done checking waveform selection.')
    if result:
        print('Optical waveform selection OK.')
    else:
        print('Optical waveform selection bad.')
    return result


# Check services.

def check_services(cfg, is_overlay):

    result = True

    for process_name in cfg:

        # Ignore any processes run in swizzler or reco1.

        if process_name == 'Swizzler':
            continue
        if process_name.find('Stage1') >= 0:
            continue

        print()
        print('Checking services for process name %s' % process_name)
        fcl_proc = cfg[process_name]
        fcl_services = fcl_proc['services']
        if 'FileCatalogMetadata' in fcl_services:
            file_type = fcl_services['FileCatalogMetadata']['fileType']
            if (is_overlay and file_type != 'overlay') or \
               (not is_overlay and file_type != 'data'):
                print('  ????? File type mismatch: %s.' % file_type)
                #result = False
            else:
                print('  File type OK.')
        else:
            print('  ***** No service FileCatalogMetadata')
            result = False
        print()

    # Done.

    return result

# Check output configuration.

def check_output(cfg):

    result = True
    print()
    print('Checking output modules.')

    # Loop over processes.

    for process_name in cfg:

        # Ignore some processes.

        if process_name == 'Swizzler':
            continue
        if process_name.find('Stage1') >= 0:
            continue
        if process_name == 'Merge':
            continue
        if process_name == 'Copy':
            continue
        if process_name.startswith('CRTMerge'):
            continue
        if process_name == 'CellTreeUB':
            continue
        if process_name == 'DLprod':
            continue

        print('Checking process name %s' % process_name)
        fcl_proc = cfg[process_name]

        # Loop over output modules in end_paths.

        if 'physics' in fcl_proc:
            fcl_physics = fcl_proc['physics']

            # Extract list of analyzer and output modules.

            analyzers = {}
            outputs = {}
            if 'analyzers' in fcl_physics:
                analyzers = fcl_physics['analyzers']
            if 'outputs' in fcl_proc:
                outputs = fcl_proc['outputs']

            if 'end_paths' in fcl_physics:
                end_paths = fcl_physics['end_paths']

                # Loop over end path modules.

                for end_path in end_paths:
                    if end_path in fcl_physics:
                        modules = fcl_physics[end_path]
                        for module in modules:
                            if not module in analyzers and not module in outputs:
                                print('  ***** Module %s not found.' % module)
                                result = False
                            elif module in outputs:
                                fcl_out = outputs[module]
                                module_type = fcl_out['module_type']
                                if module_type == 'RootOutput':

                                    if not 'saveMemoryObjectThreshold' in fcl_out:
                                        print('  ????? Parameter "saveMemoryObjectThreshold" is not defined in RootOutput.')
                                        #result = False
                                    else:
                                        sm = fcl_out['saveMemoryObjectThreshold']
                                        if sm != 0:
                                            print('  ????? Parameter "saveMemoryObjectThreshold" is present but nonzero.')
                                            #result = False
                                        else:
                                            print('  Output OK.')

    # Done

    return result


# Check Flux.

def check_flux(cfg, beam, epoch):

    result = True

    # Loop over procsss names.

    for process_name in cfg:

        print('Checking process name %s' % process_name)
        fcl_proc = cfg[process_name]

        if 'physics' in fcl_proc:
            fcl_physics = fcl_proc['physics']

            # Extract lists of module by type.

            producers = {}
            filters = {}

            if 'producers' in fcl_physics:
                producers = fcl_physics['producers']
            if 'filters' in fcl_physics:
                filters = fcl_physics['filters']

            # Loop over modules in trigger paths.

            if 'trigger_paths' in fcl_physics:
                trigger_paths = fcl_physics['trigger_paths']

                # Loop over trigger path modules.

                for trigger_path in trigger_paths:
                    if trigger_path in fcl_physics:
                        modules = fcl_physics[trigger_path]
                        for module in modules:
                            if not module in producers and not module in filters:
                                print('  ***** Module %s not found.' % module)
                                result = False
                            elif module in producers:
                                module_type = producers[module]['module_type']

                                if module_type == 'GENIEGen':

                                    print('\n  ===== Checking GENIEGen flux.')
                                    flux_path = producers[module]['FluxSearchPaths']
                                    print('  Flux path = %s' % flux_path)

                                    # Make sure flux type matches beam type.

                                    flux_path_lc = flux_path.lower()
                                    flux_type = ''
                                    if flux_path_lc.find('bnb') >= 0:
                                        flux_type = 'bnb'
                                    elif flux_path_lc.find('numi') >= 0:
                                        flux_type = 'numi'
                                    elif flux_path_lc.find('fhc') >= 0:
                                        flux_type = 'numi'
                                    elif flux_path_lc.find('rhc') >= 0:
                                        flux_type = 'numi'

                                    # All flux files in Nitish's persistent area are numi:

                                    elif flux_path.startswith('/pnfs/uboone/persistent/users/bnayak/flux_files'):
                                        flux_type = 'numi'

                                    print('  Flux type = %s' % flux_type)
                                    if flux_type != beam:
                                        print('  ***** Flux type mismatch.')
                                        result = False

                                    # Check run 4a bnb flux.

                                    if flux_type == 'bnb':
                                        r4a = (flux_path_lc.find('run4a') >= 0)
                                        if r4a:
                                            print('  Run 4a flux.')
                                        else:
                                            print('  Not run 4a flux.')
                                        if epoch == '4a' and not r4a:
                                            print('  ***** Epoch is run 4a but bnb flux is not run 4a.')
                                            result = False
                                        elif epoch != '4a' and r4a:
                                            print('  ***** Epoch is not run 4a but bnb flux is run 4a.')
                                            result = False
                                    if result:
                                        print('  Flux OK.')
                                    print()
    # Done.

    return result


# Check PMT remapping.
#
# Here is a quick synopsis of PMT remapping.
#
# PMT remapping refers to the fact that OpChannels may have a different
# interpretaiton in OpDetWaveforms vs. OpHits and OpFlashes.  This is the
# case for real data and overlay, but not for pure mc.  This programs 
# assumes that we are dealing with real data or overlay, therefomre PMT
# remapping is always required.
#
# The only action performed by this function is to check whether producer
# modules OpHitFinder and OpHitRemapProducer have been run in any given
# trigger path.  It is an error if a trigger path contains an instance
# of OpHitFinder but not OpHitRemapProducer.

def check_remap(cfg):

    result = True

    # Loop over procsss names.

    for process_name in cfg:

        # Ignore any processes run in swizzler.

        if process_name == 'Swizzler':
            continue

        # Ignore any processes run in reco1 except stand alone optical reco.

        if process_name.find('Stage1') >= 0 and not process_name.endswith('Optical'):
            continue

        print('Checking process name %s' % process_name)
        fcl_proc = cfg[process_name]

        if 'physics' in fcl_proc:
            fcl_physics = fcl_proc['physics']

            # Extract lists of module by type.

            producers = {}
            filters = {}

            if 'producers' in fcl_physics:
                producers = fcl_physics['producers']
            if 'filters' in fcl_physics:
                filters = fcl_physics['filters']

            # Loop over modules in trigger paths.

            if 'trigger_paths' in fcl_physics:
                trigger_paths = fcl_physics['trigger_paths']

                # Loop over trigger path modules.

                num_ophit = 0
                num_remap = 0
                for trigger_path in trigger_paths:
                    if trigger_path in fcl_physics:
                        modules = fcl_physics[trigger_path]
                        for module in modules:
                            if not module in producers and not module in filters:
                                print('  ***** Module %s not found.' % module)
                                result = False
                            elif module in producers:
                                module_type = producers[module]['module_type']
                                if module_type == 'OpHitFinder':
                                    #print('  Found OpHitFinder.')
                                    num_ophit += 1
                                elif module_type == 'OpHitRemapProducer':
                                    #print('  Found OpHitRemapProducer.')
                                    num_remap += 1

                        if num_ophit != 0 or num_remap != 0:
                            print('  Number of OpHitFinder modules = %d' % num_ophit)
                            print('  Number of OpHitRemapProducer modules = %d' % num_remap)
                        if num_ophit != num_remap:
                            print('  ***** PMT remap mismatch.')
                        else:
                            print('  PMT remap OK.')
                        print()

    # Done.

    return result


# Check config.
# Return True if good, False if bad.

def check_config(cfg, trigbit, beam, epoch, is_overlay,
                 do_services, do_output, do_timing, do_optical, do_flux, do_remap):

    result = True

    # Check services.

    if do_services:
        services_ok = check_services(cfg, is_overlay)
        if not services_ok:
            result = False

    # Check outputs.

    if do_output:
        output_ok = check_output(cfg)
        if not output_ok:
            result = False

    # Check beam timing.

    if do_timing and trigbit != 0 and beam != '':
        timing_ok = check_beam_timing(cfg, trigbit, beam)
        if not timing_ok:
            result = False

    # Check optical waveform selection.

    if do_optical and epoch != '':
        optical_ok = check_optical(cfg, trigbit, beam, epoch, is_overlay)
        if not optical_ok:
            result = False

    # Check flux.

    if do_flux and epoch != '' and is_overlay:
        flux_ok = check_flux(cfg, beam, epoch)
        if not flux_ok:
            result = False

    # Check PMT remapping.

    if do_remap:
        remap_ok = check_remap(cfg)
        if not remap_ok:
            result = False

    # Done.

    return result


# Determine of a file is artroot format (return True if artroot)

def is_artroot(f):
    if f in artroot_files:
        return True
    elif f in non_artroot_files:
        return False

    artroot = False

    # Try to open file as a root file.

    root = ROOT.TFile.Open(f, 'read')
    if root and root.IsOpen() and not root.IsZombie():

        # File opened successfully.
        # Loop over this file keys.
        # To qualify as an artroot file, this file must contain the following objects:
        # 1.  A TTree called 'Events'
        # 2.  A TKey called 'RootFileDB'

        events = None
        has_events = False
        has_db = False
        keys = root.GetListOfKeys()
        for key in keys:
            objname = key.GetName()
            obj = root.Get(objname)
            if objname == 'Events' and obj.InheritsFrom('TTree'):
                has_events = True
                events = obj
            if objname == 'RootFileDB' and obj.InheritsFrom('TKey'):
                has_db = True

            artroot = has_db and has_events

    # Done.

    if artroot:
        print('This is an artroot file.')
    else:
        print('This is not an artroot file.')
    return artroot


# Extract trigger bit for artroot files.

def get_trigbit(f):
    trigbit = 0
    trigbits = set()
    cmd = ['lar', '-c', 'dump_triggers.fcl', '-s', f]
    out = subprocess.check_output(cmd)
    parse = False
    for lineb in out.splitlines():
        line = larbatch_utilities.convert_str(lineb).strip()
        if line == 'Trigger bits:':
            parse = True
        elif line == '':
            parse = False

        if parse and line != 'Trigger bits:':
            words = line.split()
            if len(words) > 0:
                bit = int(words[0])
                if not bit in trigbits:
                    trigbits.add(bit)
    print()
    print('Trigger bits:', end='')
    for bit in trigbits:
        print(' %d' % bit, end='')
    print()

    # It is an error for there to be more than one trigger bit.

    if len(trigbits) == 1:
        trigbit = trigbits.pop()
    elif len(trigbits) > 1:
        print('There is more than one trigger bit.')
        trigbit == 0
    else:
        trigbit = 0
    if trigbit == 0:
        print('Unable to determine trigger bit.')

    # Done.

    return trigbit


# Get beam type based on metadata.

def get_beam(md):

    result = ''

    # Make a list of the current file name and all ancestor file names.

    filenames = set()
    filenames.add(md['file_name'])
    dim = 'isancestorof: ( file_name %s )' % md['file_name']
    ancestors = samweb.listFiles(dimensions = dim)
    for ancestor in ancestors:
        if ancestor.endswith('.ubdaq'):
            continue
        if ancestor.endswith('.crtdaq'):
            continue
        if ancestor.startswith('CRTHits'):
            continue
        if not ancestor in filenames:
            filenames.add(ancestor)

    # Loop over files.

    for f in filenames:

        # Loop for clues in file names.

        if f.lower().find('_bnb_') >= 0:
            result = 'bnb'
            print('Beam type is %s based on file name.' % result)
        elif f.lower().find('_numi_') >= 0:
            result = 'numi'
            print('Beam type is %s based on file name.' % result)
        elif f.lower().find('_rhc_') >= 0:
            result = 'numi'
            print('Beam type is %s based on file name.' % result)
        elif f.lower().find('_fhc_') >= 0:
            result = 'numi'
            print('Beam type is %s based on file name.' % result)
        if result != '':
            break

        # Look for clues in metadata.

        mdf = samweb.getMetadata(f)
        prj = mdf['ub_project.name']
        if prj.lower().find('_bnb_') >= 0:
            result = 'bnb'
            print('Beam type is %s based on sam project name.' % result)
        elif prj.lower().find('_numi_') >= 0:
            result = 'numi'
            print('Beam type is %s based on sam project name.' % result)
        elif prj.lower().find('_fhc_') >= 0:
            result = 'numi'
            print('Beam type is %s based on sam project name.' % result)
        elif prj.lower().find('_rhc_') >= 0:
            result = 'numi'
            print('Beam type is %s based on sam project name.' % result)
        if result != '':
            break

        # Look for clues in fcl file names.
        
        fcls = mdf['fcl.name']
        for fclname in fcls.split('/'):
            if fclname.lower().find('_bnb_') >= 0:
                result = 'bnb'
                print('Beam type is %s based on fcl name.' % result)
            elif fclname.lower().find('_numi_') >= 0:
                result = 'numi'
                print('Beam type is %s based on fcl name.' % result)
            if result != '':
                break
        if result != '':
            break

    # If we still haven't determined the beam type, assume it is bnb.

    if result == '':
        result = 'bnb'
        print('Last result assuming beam type is bnb.')

    # Done

    return result


# Check a single file.
# Return True if file is OK, False if not OK.

def check_file(f, md, do_crt, do_services, do_output, do_timing, do_optical,
               do_flux, do_remap):

    fname = os.path.basename(f)
    result = True

    # Extract epoch and whether or not this is mc.
    # It is an error if the epoch can not be determined.

    epoch = get_epoch(md)
    if epoch == '':
        print('Could not determine epoch.')
        result = False
    else:
        print('Epoch %s' % epoch)

    # Figure out if the beam type based on metadata.

    beam = get_beam(md)

    # Check crt merging.

    if do_crt and epoch >= '2b':

        print()
        print('Checking CRT merging.')
        crtok = check_crt_merge.check_file(fname)
        if not crtok:
            result = False

    # Figure out if this is an artroot file and also whether this is mc.

    artroot = is_artroot(f)

    # For artroot files, extract the hardware trigger bit(s).
    #
    # Common hardware trigger bits:
    # 9  - Ext
    # 11 - BNB
    # 12 - NUMI

    trigbit = 0
    if artroot:
        trigbit = get_trigbit(f)
    else:
        if beam == 'bnb':
            if md['file_type'] == 'data':
                trigbit = 11
            elif md['file_type'] == 'overlay':
                trigbit = 9
        elif beam == 'numi':
            if md['file_type'] == 'data':
                trigbit = 12
            elif md['file_type'] == 'overlay':
                trigbit = 9

    # Is this overlay?

    is_overlay = False
    if md['file_type'] == 'overlay':
        is_overlay = True

    # For artroot files, extract all fcl configurations.

    if artroot:
        print('Extracting fcl parameters.')
        fcltext = io.StringIO()
        cmd = ['config_dumper', '-P', '-s', f]
        out = subprocess.check_output(cmd)
        parse = False
        for lineb in out.splitlines():
            line = larbatch_utilities.convert_str(lineb)

            # Start processing fcl parameters after first blank line.

            if len(line) == 0:
                parse = True
            if parse:
                fcltext.write('%s\n' % line)

        # Convert fcl configuration to python dictionary.

        cfg = fcl.make_pset_str(fcltext.getvalue())
        cfgok = check_config(cfg, trigbit, beam, epoch, is_overlay,
                             do_services, do_output, do_timing, do_optical,
                             do_flux, do_remap)
        if not cfgok:
            result = False

    # Done.

    return result


# Main function.

def main(argv):

    # Statistics.

    nfile = 0
    nfileok = 0

    # Parse arguments.

    filenames = set()
    dirnames = set()
    fclname = ''
    trigbit = 0      # bnb=11, numi=12, ext=9
    beam_type = ''   # "bnb" or "numi"
    epoch = ''       # "1x", "2x", "3x", "4x", "5"
    is_overlay = False

    do_all = True
    do_crt = False
    do_services = False
    do_output = False
    do_timing = False
    do_optical = False
    do_flux = False
    do_remap = False
    skip_crt = False
    skip_services = False
    skip_output = False
    skip_timing = False
    skip_optical = False
    skip_flux = False
    skip_remap = False

    args = argv[1:]
    while len(args) > 0:
        if args[0] == '-h' or args[0] == '--help' :
            help()
            return 0
        elif (args[0] == '-f' or args[0] == '--file') and len(args) > 1:
            filename = args[1]
            if not filename in filenames:
                filenames.add(filename)
            del args[0:2]
        elif (args[0] == '-d' or args[0] == '--dir') and len(args) > 1:
            dirname = args[1]
            if not dirname in dirnames:
                dirnames.add(dirname)
            del args[0:2]
        elif (args[0] == '-c' or args[0] == '--config') and len(args) > 1:
            fclname = args[1]
            del args[0:2]
        elif (args[0] == '--trigger') and len(args) > 1:
            trigger = args[1]
            if trigger == 'bnb':
                trigbit = 11
            elif trigger == 'numi':
                trigbit = 12
            elif trigger == 'ext':
                trigbit = 9
            else:
                print('Unknown trigger type %s' % trigger)
                sys.exit(1)
            del args[0:2]
        elif (args[0] == '--beam') and len(args) > 1:
            beam = args[1]
            if beam != 'bnb' and beam != 'numi':
                print('Unknown beam type %s' % beam)
                sys.exit(1)
            del args[0:2]
        elif (args[0] == '--epoch') and len(args) > 1:
            epoch = args[1]
            if epoch != '1a' and epoch != '1b' and epoch != '1c' and \
               epoch != '2a' and epoch != '2b' and \
               epoch != '3a' and epoch != '3b' and \
               epoch != '4a' and epoch != '4b' and epoch != '4c' and epoch != '4d' and \
               epoch != '5':
                print('Unknown epoch %s' % epoch)
                sys.exit(1)
            del args[0:2]
        elif (args[0] == '--overlay'):
            is_overlay = True
            del args[0]
        elif (args[0] == '--crt'):
            do_crt = True
            do_all = False
            del args[0]
        elif (args[0] == '--services'):
            do_services = True
            do_all = False
            del args[0]
        elif (args[0] == '--output'):
            do_output = True
            do_all = False
            del args[0]
        elif (args[0] == '--timing'):
            do_timing = True
            do_all = False
            del args[0]
        elif (args[0] == '--optical'):
            do_optical = True
            do_all = False
            del args[0]
        elif (args[0] == '--flux'):
            do_flux = True
            do_all = False
            del args[0]
        elif (args[0] == '--remap'):
            do_remap = True
            do_all = False
            del args[0]
        elif (args[0] == '--no-crt'):
            skip_crt = True
            del args[0]
        elif (args[0] == '--no-services'):
            skip_services = True
            del args[0]
        elif (args[0] == '--no-output'):
            skip_output = True
            del args[0]
        elif (args[0] == '--no-timing'):
            skip_timing = True
            del args[0]
        elif (args[0] == '--no-optical'):
            skip_optical = True
            del args[0]
        elif (args[0] == '--no-flux'):
            skip_flux = True
            del args[0]
        elif (args[0] == '--no-remap'):
            skip_remap = True
            del args[0]
        else:
            print('Unknown option %s' % args[0])
            sys.exit(1)

    # Default if no options specified.

    if fclname == '' and len(filenames) == 0 and len(dirnames) == 0:
        dirnames.add('.')

    # Update action flags.

    if do_all:
        do_crt = True
        do_services = True
        do_output = True
        do_timing = True
        do_optical = True
        do_flux = True
        do_remap = True
    if skip_crt:
        do_crt = False
    if skip_services:
        do_services = False
    if skip_output:
        do_output = False
    if skip_timing:
        do_timing = False
    if skip_optical:
        do_optical = False
    if skip_flux:
        do_flux = False
    if skip_remap:
        do_remap = False

    #print('CRT      = %d' % do_crt)
    #print('Services = %d' % do_services)
    #print('Output   = %d' % do_output)
    #print('Timing   = %d' % do_timing)
    #print('Optical  = %d' % do_optical)
    #print('Flux     = %d' % do_flux)
    #print('Remap    = %d' % do_remap)

    # Make a set of filenames to check.

    files_to_check = set()

    # Add filenames.

    for filename in filenames:
        if not os.path.exists(filename):
            print('File %s does not exist.' % filename)
            sys.exit(1)
        files_to_check.add(filename)

    # Add directories.

    for dirname in dirnames:
        if not os.path.isdir(dirname):
            print('Directory %s does not exist.' % dirname)
            sys.exit(1)
        for f in os.listdir(dirname):
            if f.endswith('.root'):
                files_to_check.add(os.path.join(dirname, f))

    # Make sure fcl and files not both specified.

    if fclname != '' and len(files_to_check) > 0:
        print('Fcl and files both specified.')
        sys.exit(1)

    # If checking a fcl, name sure that trigger, beam, and epoch are specified.

    if fclname != '':
        if trigbit == 0 or beam == '' or epoch == '':
            print('Checking fcl, but trigger, beam, or epoch not specified.')
            sys.exit()

    # Check fcl configuration.

    if fclname != '':
        cfg = fcl.make_pset(fclname)

        # Add a top level key for process name.

        process_name = cfg['process_name']
        pcfg = {process_name: cfg}
        nfile += 1
        ok = check_config(pcfg, trigbit, beam, epoch, is_overlay,
                          do_services, do_output, do_timing, do_optical,
                          do_flux, do_remap)
        if ok:
            nfileok += 1        

    # Check files.

    for f in files_to_check:

        print('Checking file %s' % f)

        # Do preliminary checks to ensure that a) file exists, nd b) has sam metadata.

        if not os.path.exists(f):
            print('File does not exist.')
            sys.exit(1)

        # Extract sam metadata for this file.
        # If this file doesn't have sam metadata, skip this file (not an error).

        md = {}
        mdok = False
        ignore = False
        fname = os.path.basename(f)

        try:
            md = samweb.getMetadata(fname)
            mdok = True
            ignore = False

        except samweb_cli.exceptions.FileNotFound:

            # File not found errors are ignored.

            print('Ignoring file %s because it does not have metadata.' % fname)
            md = {}
            mkok = False
            ignore = True

        except:

            # Any other exception treat as error.

            print('Error extracting sam metadata for file %s.' % fname)
            md = {}
            mdok = False
            ignore = False

        if ignore:
            continue

        nfile += 1
        if not mdok:
            continue

        # Do further checks for this file.

        ok = check_file(f, md, do_crt, do_services, do_output, do_timing, do_optical,
                        do_flux, do_remap)
        if ok:
            nfileok += 1

    # Print statistics.

    print('\n%d files checked.' % nfile)
    print('%d files OK.' % nfileok)

    # Done.

    rc = 0
    if nfileok == nfile:
        print('Configuration checks passed.')
        rc = 0
    else:
        print('Configuration checks failed.')
        rc = 1
    return rc


# Invoke main program.

if __name__ == "__main__":
    sys.exit(main(sys.argv))
