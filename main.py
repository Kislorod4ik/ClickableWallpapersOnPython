import ctypes, os, time, datetime, requests, json, win32gui, sys
from PIL import Image, ImageDraw, ImageFont

class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_ulong), ('y', ctypes.c_ulong)]

def queryMousePosition():
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return { 'x': pt.x, 'y': pt.y}

class Cache:
    def __init__(self):
        self.filename = 'resources/cache/settings.json'
        self.checkExists()
        self.content = False
        self.cache = False
        self.read()

    def checkExists(self):
        if not os.path.exists(self.filename):
            self.createCashe()
            self.save()

    def toString(self):
        return json.dumps( self.cache, indent = 4, ensure_ascii = False )

    def writeToFile(self, content):
        f = open( self.filename, 'w', encoding = 'utf8' )
        f.write( content )
        f.close()
               

    def save(self):
        self.writeToFile( self.toString() )

    def readFile(self):
        f = open(self.filename, 'r', encoding = 'utf8')
        self.content = f.read()
        f.close()  

    def read(self, i = 0):
        if i > 1:
            print('Error read cache file.')
            sys.exit()
        self.readFile()    
        try:
            self.cache = json.loads( self.content )
        except:     
            self.createCashe()
            self.save()
            return self.read(i + 1)           
    
    def createCashe(self):
        self.cache = {
            'version': 'v1.0'           
        }
    
    def get(self, index, default):
        if index in self.cache:
            return self.cache[index]
        self.put( index, default )
        return default
        
    def put(self, index, body):
        self.cache[index] = body
        self.save()
    
cache = Cache()    
        
class Course:
    
    def getJsonData():
        url = 'https://www.cbr-xml-daily.ru/daily_json.js'
        return requests.get(url, headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}).json()
    
    def getCourse(args):
        try:
            data = Course.getJsonData()
            tbl = []
            for i in args:
                tbl.append( (i.upper(), round(data['Valute'][ i.upper() ]['Value'], 2)))
            return tbl
        except:
            return False

class Weather:
    
    def getCitys():
        return cache.get('weather', [
            ['Самара', 'https://www.gismeteo.ru/weather-samara-4618/'],
            ['Тольятти', 'https://www.gismeteo.ru/weather-tolyatti-4429/'],
            ['Москва', 'https://www.gismeteo.ru/weather-moscow-4368/']
        ])
    
    city = getCitys()[ cache.get('weatherIndex', 0) ]
    
    def setCity(index):
        Weather.city = Weather.getCitys()[index]
    
    def getJsonData():
        try:
            data = requests.get(Weather.city[1], headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}).text
            i = str.find(data, 'M.state.weather.cw = {')
            if i == -1:
                return False
            end = str.find(data[i:], '\n')
            if end == -1:
                return False
            return json.loads( data[i + 21: i + end] ) 
        except:
            return False

    def getData():
        try:
            info = Weather.getJsonData()
            return Weather.city[0], info['temperatureAir'][0], info['description'][0]
        except:
            return False

class Date:
    
    def getDay():
        return ([
            'Понедельник',
            'Вторник',
            'Среда',
            'Четверг',
            'Пятница',
            'Суббота',
            'Восскресенье'
        ])[datetime.datetime.today().isoweekday() - 1]
        
    def get(*formats):
        date = datetime.datetime.now()
        if len(formats) == 1:
            return date.strftime(formats[0])
        back = []    
        for i in formats:
            back.append( date.strftime(i) )
        return tuple(back)
        

class Color:
   
    def hex(hex):
        hex = hex.lstrip('#')
        hlen = len(hex)
        return tuple(int(hex[i:i+int(hlen/3)], 16) for i in range(0, hlen, int(hlen/3)))  

    def getThemeList():
        return [
            { 'bg': Color.hex('#131313'), 'fg': Color.hex('#980002'), 'text': Color.hex('#ffbf00') },
            { 'bg': Color.hex('#ebdcb2'), 'fg': Color.hex('#af4425'), 'text': Color.hex('#552e1c') },
            { 'bg': Color.hex('#1e0000'), 'fg': Color.hex('#bc6d4f'), 'text': Color.hex('#9d331f') },
            { 'bg': Color.hex('#ddc5a2'), 'fg': Color.hex('#523634'), 'text': Color.hex('#b6452c') },
            { 'bg': Color.hex('#003b46'), 'fg': Color.hex('#c3dfe6'), 'text': Color.hex('#66a5ad') }
        ]

    def getTheme( mode ):
        return Color.getThemeList()[mode]

class Cord:

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.x2 = x + w
        self.y2 = y + h
        
    def isInside(self, x, y ):
        return x >= self.x and x <= self.x2 and y >= self.y and y <= self.y2

class Main():

    def __init__(self):
    
        user32 = ctypes.windll.user32
        
        self.weight = user32.GetSystemMetrics(0)
        self.height = user32.GetSystemMetrics(1)
       
        self.mBuffer = user32.GetKeyState(1)
        self.mPos = False
        self.mDown = False
        
        self.path = os.getcwd()
        self.indexTheme = cache.get('themeIndex', 0)
        self.theme = Color.getTheme(self.indexTheme)
        
        self.font = ImageFont.load_default()
        self.cashFonts = {}
        
        self.bg = False
        self.bgLastColor = False
        
        self.buttons = []
        
    def addButton(self, cord, function, update):
        self.buttons.append({'cord': cord, 'function': function, 'update': update})
        
    def genEmpty(self):
        if not self.bg or self.theme['bg'] != self.bgLastColor:
            color = self.theme['bg']
            img = Image.new('RGB', (self.weight, self.height), color)
            self.orig = img

        
        img = self.orig.copy()
 
        self.object = img
        self.draw = ImageDraw.Draw(img)
    
    
    def getTextSize(self, text):
        return self.draw.textsize(text, self.font)
        
    def setFont(self, name, size):
        id = f'{name}x{size}'
        if not id in self.cashFonts:
            self.cashFonts[id] = ImageFont.truetype(f'resources/fonts/{name}', size)
        self.font = self.cashFonts[id] 
    
    def setText(self, x, y, text, color = (255, 255, 255),):
        self.draw.text((x, y), text, font = self.font, fill = color)
        w, h = self.getTextSize( text )
        return Cord(x, y, w, h)
        
    def setMindText(self, x, y, text, color = (255, 255, 255)):
        w, h = self.getTextSize( text )
        return self.setText( int(x - w / 2), y, text, color )

    def setWallpaper(self, filename):
        ctypes.windll.user32.SystemParametersInfoW(0x0014 , 0, self.path + f'\\{filename}', 2)

    def onUpdate(self):
        self.pos = queryMousePosition()
        ctypes.windll.user32.GetKeyState.restype = ctypes.c_ushort
        if ctypes.windll.user32.GetKeyState(1) != self.mBuffer:
            self.mBuffer = bool(abs(int(self.mBuffer) - 1))
            self.mDown = True

        back = False    
        if self.mDown:
            self.mDown = False
            focus = win32gui.GetWindowText( win32gui.GetForegroundWindow() )
            if focus in {'Program Manager', ''} :
                x, y = self.pos['x'], self.pos['y'] 
                for butt in self.buttons:
                    if butt['cord'].isInside(x, y):
                        butt['function']()
                        if butt['update']:
                            back = True
        return back                
                

    def start(self):
    
        self.openCitys = False
        
        def cityBtn():
            self.openCitys = True
            
        def setCity(index):
            Weather.setCity( index )
            self.openCitys = False
            cache.put('weatherIndex', index)
       
        def newTheme():
            self.indexTheme += 1
            if self.indexTheme == len(Color.getThemeList()):
                self.indexTheme = 0 
            self.theme = Color.getTheme(self.indexTheme)
            cache.put('themeIndex', self.indexTheme)
       
        while True:
            self.buttons = []
            c2 = False
            self.genEmpty()
            
            minutes, H_M, d_m_Y = Date.get('%M', '%H:%M', '%d.%m.%Y' )

            w = self.weight / 2
            theme = self.theme

            self.setFont( 'font.otf', 100 )

            c = self.setMindText( w , self.height / 3 - 100, Date.getDay(), theme['fg'])
            
            courses = Course.getCourse(cache.get('courses',  ['USD', 'EUR']))
            if courses:
                self.setFont( 'font.otf', 50 )
                c2 = self.setMindText( w , c.y2 + 15, '  '.join([ f'{i[0]}: {str(i[1])}' for i in courses ]), theme['fg'])
                
                self.draw.line(( min(c.x, c2.x) - 10, c2.y2 + 15,  max(c.x2, c2.x2) + 10, c2.y2 + 15), fill = theme['fg'], width=5)
            else:
                self.draw.line(( c.x - 10, c.y2 + 15, c.x2 + 10, c.y2 + 15), fill = theme['fg'], width=5)
            
            
            self.setFont( 'font.otf', 100 )
            c = self.setMindText( w , (c2.y2 if c2 else c.y2 ) + 30, H_M, theme['fg'])
            
            self.setFont( 'font.otf', 45 )
            c = self.setMindText( w , c.y2 + 20, d_m_Y, theme['fg'])
            
            self.setFont( 'font.ttf', 20 )
            w1, h1 = self.getTextSize('Сменить тему')
            s = self.setText( self.weight - 5 - w1, self.height - 48 - h1, 'Сменить тему', theme['fg'])
            self.addButton(s, lambda: newTheme(), True)
            
            if not self.openCitys:
                self.setFont( 'font.otf', 40 )
                name, temp, info = Weather.getData()
                if name:
                    s = self.setText(5, 5, str(name), theme['text'])
                    self.addButton(s, cityBtn, True)
                    self.setText(5, s.y2 + 5, f'{str(temp)}° {str(info)}', theme['text'])
            else:
                self.setFont( 'font.ttf', 25 )
                s = self.setText(5, 5, 'Выберите населённый пункт', theme['fg'])
                tbl = Weather.getCitys()
                for i in range(len(tbl)):
                    s = self.setText(10, s.y2 + 5, tbl[i][0], theme['text'])  
                    self.addButton(s, lambda index = i: setCity(index), True)
            
            
            self.object.save('resources/tmp/temp.png')
            self.setWallpaper('resources/tmp/temp.png')

            while minutes == Date.get('%M') and not self.onUpdate():
                time.sleep(0.1)
        
        
if __name__ == "__main__":
    main = Main()
    main.start()
