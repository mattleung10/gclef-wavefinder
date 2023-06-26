from tkinter import Label, PhotoImage, Tk, ttk

from PIL import Image, ImageTk

from MightexBufCmos import Camera


# function for video streaming
def video_stream(camera : Camera, lmain : ttk.Label):
    camera.acquire_frames()
    if camera.has_frames():
        frame = camera.get_frame()
        img = Image.fromarray(frame.img)
        imgtk = ImageTk.PhotoImage(image=img)
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
    lmain.after(1, video_stream, camera, lmain)


if __name__ == "__main__":

    # make Tkinter frame
    root = Tk()
    frm = ttk.Frame(root, padding=20)
    frm.grid()
    ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
    ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
    lmain = ttk.Label(frm)
    lmain.grid(column=1,row=1)

    # set up camera
    camera = Camera()
    camera.print_introduction()

    # start streaming
    video_stream(camera, lmain)
    root.mainloop()
