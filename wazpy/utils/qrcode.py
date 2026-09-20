class QRCode:
    def __init__(self, data, nodeJS):
        self.data = data["qr"]
        self.nodeJS = nodeJS

    def render(self, small: bool = True):
        if not isinstance(small, bool):
            raise TypeError("qrSmall must be boolean")
        
        response = self.nodeJS.send({
            "action": "qrcodeGenerate",
            "type": "terminal",
            "qr": self.data,
            "small": small
        })

        if not response["success"]:
            raise RuntimeError(response.get("message", "Failed to create a image for QRCode"))


    def saveImg(self, imgName: str = "qr.png", imgWidth: int = 500):
        if not isinstance(imgWidth, int):
            raise TypeError("imgWidth must be a integer")
        
        response = self.nodeJS.send({
            "action": "qrcodeGenerate",
            "type": "img",
            "qr": self.data,
            "fileName": str(imgName),
            "fileWidth": imgWidth
        })

        if not response["success"]:
            raise RuntimeError(response.get("message", "Failed to create a image for QRCode"))