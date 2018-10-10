from abc import ABC, abstractmethod
import numpy as np

class RecordingExtractor(ABC):
    '''A class that contains functions for extracting important information
    from recorded extracellular data. It is an abstract class so all
    functions with the @abstractmethod tag must be implemented for the
    initialization to work.


    '''
    def __init__(self):
        self._epochs = {}

    @abstractmethod
    def getTraces(self, start_frame=None, end_frame=None, channel_ids=None):
        '''This function extracts and returns a trace from the recorded data from the
        given channels ids and the given start and end frame. It will return
        traces from within three ranges:

            [start_frame, t_start+1, ..., end_frame-1]
            [start_frame, start_frame+1, ..., final_recording_frame - 1]
            [0, 1, ..., end_frame-1]
            [0, 1, ..., final_recording_frame - 1]

        if both start_frame and end_frame are given, if only start_frame is
        given, if only end_frame is given, or if neither start_frame or end_frame
        are given, respectively. Traces are returned in a 2D array that
        contains all of the traces from each channel with dimensions
        (num_channels x num_frames). In this implementation, start_frame is inclusive
        and end_frame is exclusive conforming to numpy standards.

        Parameters
        ----------
        start_frame: int
            The starting frame of the trace to be returned (inclusive).
        end_frame: int
            The ending frame of the trace to be returned (exclusive).
        channel_ids: array_like
            A list or 1D array of channel ids (ints) from which each trace will be
            extracted.

        Returns
        ----------
        traces: numpy.ndarray
            A 2D array that contains all of the traces from each channel.
            Dimensions are: (num_channels x num_frames)
        '''
        pass

    @abstractmethod
    def getNumChannels(self):
        '''This function returns the number of channels in the recording.

        Returns
        -------
        num_channels: int
            Number of channels in the recording.
        '''
        pass

    @abstractmethod
    def getNumFrames(self):
        '''This function returns the number of frames in the recording.

        Returns
        -------
        num_frames: int
            Number of frames in the recording (duration of recording).
        '''
        pass

    @abstractmethod
    def getSamplingFrequency(self):
        '''This function returns the sampling frequency in units of Hz.

        Returns
        -------
        fs: float
            Sampling frequency of the recordings in Hz.
        '''
        pass

    def frameToTime(self, frame):
        '''This function converts a user-inputted frame index to a time with units of seconds.

        Parameters
        ----------
        frame: float
            The frame to be converted to a time.

        Returns
        -------
        time: float
            The corresponding time in seconds.
        '''
        # Default implementation
        return frame/self.getSamplingFrequency()

    def timeToFrame(self, time):
        '''This function converts a user-inputted time (in seconds) to a frame index.

        Parameters
        -------
        time: float
            The time (in seconds) to be converted to frame index.

        Returns
        -------
        frame: float
            The corresponding frame index.
        '''
        # Default implementation
        return time*self.getSamplingFrequency()

    def getSnippets(self, snippet_len_before, snippet_len_after, start_frames, channel_ids=None):
        '''This function returns data snippets from the given channels that
        are starting on the given frames and are the length of the given snippet
        lengths before and after.

        Parameters
        ----------
        snippet_len_before: int
            The number of frames before the start frame (inclusive)
        snippet_len_after: int
            The number of frames after the start frame (exclusive)
        start_frames: array_like
            A list or array of frames that will be used as the start frame of
            each snippet.
        channel_ids: array_like
            A list or array of channel ids (ints) from which each trace will be
            extracted.

        Returns
        ----------
        snippets: numpy.ndarray
            Returns a list of the snippets as numpy arrays.
            The length of the list is len(start_frames)
            Each array has dimensions: (num_channels x snippet_len)
            Out-of-bounds cases should be handled by filling in zeros in the snippet.
        '''
        # Default implementation
        if channel_ids is None:
            channel_ids = range(self.getNumChannels())

        num_snippets = len(start_frames)
        num_channels = len(channel_ids)
        num_frames = self.getNumFrames()
        snippets = []
        snippet_len = snippet_len_before + snippet_len_after
        for i in range(num_snippets):
            snippet_chunk = np.zeros((num_channels,snippet_len))
            if (0<=start_frames[i]) and (start_frames[i]<num_frames):
                snippet_range = np.array([int(start_frames[i])-snippet_len_before, int(start_frames[i])+snippet_len_after])
                snippet_buffer = np.array([0,snippet_len])
                # The following handles the out-of-bounds cases
                if snippet_range[0] < 0:
                    snippet_buffer[0] -= snippet_range[0]
                    snippet_range[0] -= snippet_range[0]
                if snippet_range[1] >= num_frames:
                    snippet_buffer[1] -= snippet_range[1] - num_frames
                    snippet_range[1] -= snippet_range[1] - num_frames
                snippet_chunk[:,snippet_buffer[0]:snippet_buffer[1]] = self.getTraces(start_frame=snippet_range[0],
                                                                                      end_frame=snippet_range[1],
                                                                                      channel_ids=channel_ids)
            snippets.append(snippet_chunk)

        return snippets

    def getChannelInfo(self, channel_id):
        '''This function returns the a dictionary containing information about
        the channel specified by the channel id. Important keys in the dict to
        fill out should be: 'group', 'position', and 'type'.

        Parameters
        ----------
        channel_id: int
            The channel id of the channel for which information is returned.

        Returns
        ----------
        channel_info_dict: dict
            A dictionary containing important information about the specified
            channel. Should include:

                    key = 'group', type = int
                        the group number it is in, for tetrodes

                    key = 'position', type = array_like
                        two/three dimensional

                    key = 'type', type = string
                        recording ('rec') or reference ('ref')
        '''
        raise NotImplementedError("The getChannelInfo function is not \
                                  implemented for this extractor")

    def addEpoch(self, epoch_name, start_frame, end_frame):
        '''This function adds an epoch to your recording extractor that tracks
        a certain time period in your recording. It is stored in an internal
        dictionary of start and end frame tuples.

        Parameters
        ----------
        epoch_name: str
            The name of the epoch to be added
        start_frame: int
            The start frame of the epoch to be added (inclusive)
        end_frame: int
            The end frame of the epoch to be added (exclusive)

        '''
        #Default implementation only allows for frame info. Can override to put more info
        if(isinstance(epoch_name, str)):
            self._epochs[epoch_name] = {'start_frame': int(start_frame), 'end_frame': int(end_frame)}
        else:
            raise ValueError("epoch_name must be a string")

    def removeEpoch(self, epoch_name):
        '''This function removes an epoch from your recording extractor.

        Parameters
        ----------
        epoch_name: str
            The name of the epoch to be removed
        '''
        if(isinstance(epoch_name, str)):
            if(epoch_name in list(self._epochs.keys())):
                del self._epochs[epoch_name]
            else:
                raise ValueError("This epoch has not been added")
        else:
            raise ValueError("epoch_name must be a string")

    def getEpochNames(self):
        '''This function returns a list of all the epoch names in your recording

        Returns
        ----------
        epoch_names: list
            List of epoch names in the recording extractor
        '''
        epoch_names = list(self._epochs.keys())
        if not epoch_names:
            pass
        else:
            epoch_start_frames = []
            for epoch_name in epoch_names:
                epoch_info = self.getEpochInfo(epoch_name)
                start_frame = epoch_info['start_frame']
                epoch_start_frames.append(start_frame)
            epoch_names = [epoch_name for _,epoch_name in sorted(zip(epoch_start_frames,epoch_names))]
        return epoch_names

    def getEpochInfo(self, epoch_name):
        '''This function returns the start frame and end frame of the epoch
        in a dict.

        Parameters
        ----------
        epoch_name: str
            The name of the epoch to be returned

        Returns
        ----------
        epoch_info: dict
            A dict containing the start frame and end frame of the epoch
        '''
        #Default (Can add more information into each epoch in subclass)
        if(isinstance(epoch_name, str)):
            if(epoch_name in list(self._epochs.keys())):
                epoch_info = self._epochs[epoch_name]
                return epoch_info
            else:
                raise ValueError("This epoch has not been added")
        else:
            raise ValueError("epoch_name must be a string")

    def getEpoch(self, epoch_name):
        '''This function returns a SubRecordingExtractor which is a view to the
        given epoch

        Parameters
        ----------
        epoch_name: str
            The name of the epoch to be returned

        Returns
        ----------
        epoch_extractor: SubRecordingExtractor
            A SubRecordingExtractor which is a view to the given epoch
        '''
        epoch_info = self.getEpochInfo(epoch_name)
        start_frame = epoch_info['start_frame']
        end_frame = epoch_info['end_frame']
        from .SubRecordingExtractor import SubRecordingExtractor
        return SubRecordingExtractor(parent_extractor=self, start_frame=start_frame,
                                     end_frame=end_frame)

    @staticmethod
    def writeRecording(self, recording_extractor, save_path):
        '''This function writes out the recorded file of a given recording
        extractor to the file format of this current recording extractor. Allows
        for easy conversion between recording file formats. It is a static
        method so it can be used without instantiating this recording extractor.

        Parameters
        ----------
        recording_extractor: RecordingExtractor
            An RecordingExtractor that can extract information from the recording
            file to be converted to the new format.

        save_path: string
            A path to where the converted recorded data will be saved, which may
            either be a file or a folder, depending on the format.
        '''
        raise NotImplementedError("The writeRecording function is not \
                                  implemented for this extractor")