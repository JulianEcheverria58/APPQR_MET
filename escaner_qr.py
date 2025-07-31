# escaner_qr.py
import cv2
from pyzbar.pyzbar import decode
import requests
import webbrowser

def escanear_qr():
    cap = cv2.VideoCapture(0)
    
    while True:
        _, frame = cap.read()
        decoded_objects = decode(frame)
        
        for obj in decoded_objects:
            url = obj.data.decode('utf-8')
            print(f"URL detectada: {url}")
            webbrowser.open(url)
            cap.release()
            cv2.destroyAllWindows()
            return
        
        cv2.imshow("QR Scanner", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    escanear_qr()