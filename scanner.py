#!/usr/bin/env python3

'''Uses a video camera as a barcode scanner

   opencv for the video camera interface and image display
   pyzbar for barcode scanning
   simpleaudio for audio feedback
'''

import logging
import time
import datetime
import os.path

import cv2
from pyzbar.pyzbar import decode
import simpleaudio


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', '-s', default=False, action='store_true', help='Exit upon successful scan')
    parser.add_argument('--output', '-o', default=False, action='store_true', help='Write to CSV file')
    parser.add_argument('--output_path', '-p', default='.', help='Path to write the CSV file - defaults to the current path')
    parser.add_argument('--mute', '-m', default=False, action='store_true', help='Suppress the confirmation beep')
    parser.add_argument('--no_flip', default=False, action='store_true', help='Do not horizontally flip the image')
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARN)

    # Load scanner beep sound
    assetPath = os.path.join(os.path.dirname(os.path.join(os.path.realpath(__file__))), 'assets')
    beepWave = simpleaudio.WaveObject.from_wave_file(os.path.join(assetPath, 'scannerBeep.wav'))

    # Create a VideoCapture object and read from input file
    # If the input is the camera, pass 0 instead of the video file name
    cap = cv2.VideoCapture(0)

    # Check if camera opened successfully
    if (cap.isOpened()== False): 
        print("Error opening video stream or file")

    # Read until CTRL-C pressed
    frameIndex = 0
    codeIndex = 0

    # Require a certain number of scans in an interval to guarantee confidence
    requiredScans = 2
    scanInterval = 5
    dataBuffer = {}
    # acceptedTypes = set(['EAN13', 'UPCA'])

    holdoffTime = 20
    holdoffBuffer = {}

    # Open file for write
    if args.output:
        outputFilename = os.path.join(args.output_path, f"barcodes_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv")
        print(f'\nWriting to {outputFilename}...')
        outputFile = open(outputFilename, 'w')
        outputFile.write('timestamp,code,type\n')

    if not args.single:
        print('\n*** Press CTRL-C or q to exit')

    # Main scanner loop
    while(cap.isOpened()):
        try:
            # Capture frame-by-frame
            ret, frame = cap.read()
            if ret == True:
                results = decode(frame)
                
                # Add results to data buffer
                if len(results) > 0:
                    # Process and print results
                    for result in results:
                        curData = result.data.decode('utf-8'), result.type

                        # Check if in holdoff buffer - if so, ignore and update holdoff
                        if curData in holdoffBuffer:
                            holdoffBuffer[curData] = frameIndex
                            break

                        # Check if in buffer
                        if curData in dataBuffer:
                            dataBuffer[curData].append(frameIndex)
                        else:
                            dataBuffer[curData] = [frameIndex]
                        
                        logging.debug(f'Frame {frameIndex}: Add {curData[0]} ({curData[1]}), Readings: {dataBuffer[curData]}')

                # Remove old readings from data buffer
                oldestIndex = frameIndex - scanInterval
                for key, readings in dataBuffer.items():
                    newReadings = []
                    for reading in readings:
                        if reading >= oldestIndex:
                            newReadings.append(reading)
                        else:
                            logging.debug(f'Frame {frameIndex}: Drop {key[0]} ({key[1]}), Frame {reading}')
                    dataBuffer[key] = newReadings

                # Check data buffer for valid results
                itemsToRemove = []
                for key, readings in dataBuffer.items():
                    code, codeType = key
                    if len(readings) >= requiredScans:

                        # Print out the result
                        print(f'\nBarcode {codeIndex+1}: {code} ({codeType})')

                        # Play a sound to indicate success
                        if not args.mute:
                            beepWave.play()
                        
                        # Write to file
                        if args.output:
                            outputFile.write(f'{time.time():.6f},{code},{codeType}\n')

                        codeIndex += 1

                        holdoffBuffer[key] = readings[-1]

                        itemsToRemove.append(key)

                        if args.single:
                            break

                    elif len(readings) == 0:
                        itemsToRemove.append(key)

                # Remove items with no valid readings
                for item in itemsToRemove:
                    logging.debug(f'Frame {frameIndex}: Del {item[0]} ({item[1]}), Readings: {dataBuffer[item]}')
                    del(dataBuffer[item])

                # Update holdoff buffer
                holdoff = frameIndex - holdoffTime
                itemsToRemove = []
                for key, lastFrame in holdoffBuffer.items():
                    if lastFrame < holdoff:
                        itemsToRemove.append((key, lastFrame))
                for key, lastFrame in itemsToRemove:
                    logging.debug(f'Frame {frameIndex}: Holdoff Drop {key[0]} ({key[1]}), Last frame {lastFrame}')
                    del(holdoffBuffer[key])

                # If in single scan mode, break if scan is successful
                if args.single and codeIndex > 0:
                    break

                frameIndex = frameIndex + 1

                # Display the resulting frame
                if not args.no_flip:
                    frame = cv2.flip(frame, 1)
                cv2.imshow('Scanner', frame)

                # Press Q on keyboard to  exit
                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break

            # Break the loop
            else: 
                break
        except KeyboardInterrupt:
            break

    if args.output:
        print(f'\nClosing output file: {outputFilename}')
        outputFile.close()

    # When everything done, release the video capture object
    cap.release()

    # Closes all the frames
    cv2.destroyAllWindows()

    print('\nDone.\n')
