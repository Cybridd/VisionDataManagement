import Image as im
import Video

def main():
    vid = Video.Video("E:/MScProject/Test/Nina/Data/Gnocchi2_3v/fullstream.mp4","rgb")
    #print(vid.name)
    #print(vid.filepath.split("/")[0])
    vid.getFrames()
    #for frame in vid.frames:
    #    print(frame)
    vid.saveFramesImageOnly()

if __name__ == '__main__':
    main()
