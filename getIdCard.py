#!coding=UTF-8

# ------------------------------------------------------------------
# Title        随机身份证号生成API
# Author    chenqiwei
# Created   2022/07/05
# Update    2022/07/05
# ------------------------------------------------------------------

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib import request
import io,shutil,json,re,time,random,os

class MyHttpHandler(BaseHTTPRequestHandler):

    def writeJson(self, code, content='', message=''):
        ''' 输出json内容 '''
        if content == '':
            content = {}
        if message == '' and code == 200:
            message = '请求成功'
        elif message == '' and code == 500:
            message = '服务器异常'
        outContent = json.dumps({"code": code, "data": content, "message": message},ensure_ascii=False).encode("UTF-8")  # 定义json结构
        f = io.BytesIO()
        f.write(outContent)
        f.seek(0)
        self.send_response(code)
        self.send_header("Content-type", "application/json; charset=UTF-8")
        self.send_header("Content-Length", str(len(outContent)))
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)

    def notFound(self):
        ''' 输出404 '''
        self.writeJson(404, '', '路径不存在')

    def getPostValue(self, data, key):
        ''' 获取请求头的post值 '''
        if self.command != 'POST':
            return ''
        contentInfo = data.decode()
        reCon = re.findall(r'Content-Disposition: form-data; name="(.*?)"(.*?)\r\n\r\n(.*?)\r\n', contentInfo, re.DOTALL)
        content = ''
        for name in reCon:
            if key == name[0]:
                content = name[2]
                break
        return content

    def leapYear(self, year):
        ''' 是否为闰年 '''
        if year % 4 == 0 and year % 400 == 0:
            return True
        elif year % 4 == 0 and year % 100 != 0:
            return True
        else:
            return False

    def provinceCode(self, province=''):
        ''' 返回指定省份名称和区号'''
        provinceCode = {'北京市': 110000, '天津市': 120000, '河北省': 130000, '山西省': 140000, '内蒙古自治区': 150000, '辽宁省': 210000, '吉林省': 220000, '黑龙江省': 230000, '上海': 310000, '江苏省': 320000, '浙江省': 330000, '安徽省': 340000, '福建省': 350000, '江西省': 360000, '山东省': 370000, '河南省': 410000, '湖北省': 420000,'湖南省': 430000, '广东省': 440000, '广西壮族自治区': 450000, '海南省': 460000, '重庆市': 500000, '四川省': 510000, '贵州省': 520000, '云南省': 530000, '西藏自治区': 540000, '陕西省': 610000, '甘肃省': 620000, '青海省': 630000, '宁夏回族自治区': 640000, '新疆维吾尔自治区': 650000, '台湾省': 710000, '香港特别行政区': 810000, '澳门特别行政区': 820000}
        if (province == ''):
            provinceName = random.choice(list(provinceCode.keys()))
            province = provinceCode[provinceName]
            return {'code': province, 'name': provinceName}
        else:
            default = ''
            return {'code': provinceCode.get(province, default), 'name': province}

    def codeApi(self, code):
        ''' 根据父级区号查询子级区号API '''
        info = request.urlopen(
            'https://quhua.ipchaxun.com/api/areas/data?parentcode=' + str(code) + '&children=1')
        return json.loads(info.read())

    def getDistrictCode(self, province, city, district):
        ''' 处理区域 '''
        sar = [710000, 810000, 820000]
        municipality = [110000, 120000, 310000, 500000]
        if(province == ''):
            # 处理省
            provinceCode = self.provinceCode()
            province = self.codeApi(provinceCode['code'])['data']['results']
            # 处理市
            city = province[random.randint(0, len(province)-1)]
            # 处理区县
            districts = city['childrens'][random.randint(0, len(city['childrens'])-1)]
            return {
                'code': districts['code'],
                'provinceName':  provinceCode['name'],
                'cityName': city['name'],
                'districtName': districts['name']
            }
        elif(city == ''):
            # 处理省
            provinceCode = self.provinceCode(province)
            province = provinceCode['code']
            if(province == ''):
                return self.writeJson(500, '', '请填写正确的省份名称')
            elif province in sar:
                return {
                    'code': province,
                    'provinceName': provinceCode['name'],
                    'cityName': provinceCode['name'],
                    'districtName': provinceCode['name']
                }
            province = self.codeApi(province)['data']['results']
            # 处理市
            city = province[random.randint(0, len(province)-1)]
            # 处理区县
            districts = city['childrens'][random.randint(0, len(city['childrens'])-1)]
            district = districts['code']
            return {
                'code': district,
                'provinceName': provinceCode['name'],
                'cityName': city['name'],
                'districtName': districts['name']
            }
        elif(district == ''):
            # 处理省
            provinceCode = self.provinceCode(province)
            province = provinceCode['code']
            if(province == ''):
                return self.writeJson(500, '', '请填写正确的省份名称')
            elif province in sar:
                return {
                    'code': province,
                    'provinceName': provinceCode['name'],
                    'cityName': provinceCode['name'],
                    'districtName': provinceCode['name']
                }
            provinces = self.codeApi(province)['data']['results']
            if province in municipality:
                provinces = provinces[0]['childrens']
            # 处理市
            index = 0
            for list in provinces:
                if list['name'] == city:
                    isCity = True
                    city = list['name']
                    break
                isCity = False
                index += 1
            if(isCity == False):
                return self.writeJson(500, '', '请填写正确的市名')
            # 处理区县
            if province in municipality:
                return {
                    'code': provinces[index]['code'],
                    'provinceName': provinceCode['name'],
                    'cityName': provinceCode['name'],
                    'districtName': provinces[index]['name']
                }
            districts = provinces[index]['childrens']
            districts = districts[random.randint(0, len(districts)-1)]
            return {
                'code': districts['code'],
                'provinceName': provinceCode['name'],
                'cityName': city,
                'districtName': districts['name']
            }
        else:
            # 处理省
            provinceCode = self.provinceCode(province)
            province = provinceCode['code']
            if(province == ''):
                return self.writeJson(500, '', '请填写正确的省份名称')
            elif province in sar:
                return {
                    'code': province,
                    'provinceName': provinceCode['name'],
                    'cityName': provinceCode['name'],
                    'districtName': provinceCode['name']
                }
            provinces = self.codeApi(province)['data']['results']
            if province in municipality:
                provinces = provinces[0]['childrens']
            # 处理市
            index = 0
            for list in provinces:
                if list['name'] == city:
                    isCity = True
                    city = list['name']
                    break
                isCity = False
                index += 1
            if(isCity == False):
                return self.writeJson(500, '', '请填写正确的市名')
            # 处理区县
            if province in municipality:
                return {
                    'code': provinces[index]['code'],
                    'provinceName': provinceCode['name'],
                    'cityName': provinceCode['name'],
                    'districtName': provinces[index]['name']
                }
            districts = provinces[index]['childrens']
            index = 0
            for list in districts:
                if list['name'] == district:
                    isDistrict = True
                    break
                isDistrict = False
                index += 1
            if(isDistrict == False):
                return self.writeJson(500, '', '请填写正确的区县名')
            districts = districts[index]
            return {
                'code': districts['code'],
                'provinceName': provinceCode['name'],
                'cityName': city,
                'districtName': districts['name']
            }

    def getYear(self, year):
        ''' 处理年份 '''
        nowYear = time.strftime('%Y', time.localtime())
        if year == '':
            return random.randint(1949, int(nowYear)-16)
        try:
            year = int(year)
        except:
            return self.writeJson(500, '', '年份格式错误，请输入整数')
        if(1949 <= year <= int(nowYear)-16):
            return year
        return self.writeJson(500, '', '年份必须大于等于1949且小于等于' + int(nowYear)-16)

    def getMonth(self, month):
        ''' 处理月份 '''
        if month == '':
            return random.randint(1, 12)
        try:
            month = int(month)
        except:
            return self.writeJson(500, '', '月份格式错误，请输入整数')
        if(1 <= month <= 12):
            return month
        return self.writeJson(500, '', '月份必须大于等于1且小于等于12')

    def getDay(self, year, month, day):
        ''' 处理日 '''
        if day == '':
            return random.randint(1, 28)
        try:
            day = int(day)
        except:
            return self.writeJson(500, '', '日格式错误，请输入整数')
        if month == 2:
            if self.leapYear(year) and day > 28:
                return self.writeJson(500, '', '该月份与天数不一致，请检查')
            elif day > 29:
                return self.writeJson(500, '', '该月份与天数不一致，请检查')
            else:
                return day
        elif (month in [1, 3, 5, 7, 8, 10, 12] and day <= 31):
            return day
        elif (month in [4, 6, 9, 11] and day <= 30):
            return day
        else:
            return self.writeJson(500, '', '该月份与天数不一致，请检查')

    def getSex(self, sex):
        ''' 处理性别 '''
        if (sex != '男' and sex != '女'):
            list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            num = random.sample(list, 1)[0]
            if (num % 2) == 0:
                type = 0
            else:
                type = 1
            return {'sex': num, 'type': type}
        else:
            if sex == '男':
                list = [1, 3, 5, 7, 9]
                return {'sex': random.sample(list, 1)[0], 'type': 1}
            list = [0, 2, 4, 6, 8]
            return {'sex': random.sample(list, 1)[0], 'type': 2}

    def do_GET(self):
        ''' 处理get请求 '''
        self.notFound()

    def do_POST(self):
        ''' 处理post请求 '''
        path = os.path.basename(os.path.realpath(__file__)).split('.')[0]
        if (self.path == "/"+path):
            # 接收传参
            datas = self.rfile.read(int(self.headers['content-length']))
            code = self.getDistrictCode(self.getPostValue(datas, 'province'), self.getPostValue(datas, 'city'), self.getPostValue(datas, 'district'))
            year = self.getYear(self.getPostValue(datas, 'year'))
            month = self.getMonth(self.getPostValue(datas, 'month'))
            day = self.getDay(year, month, self.getPostValue(datas, 'day'))
            sex = self.getSex(self.getPostValue(datas, 'sex'))
            # 第16-17位随机
            other = random.randint(10, 99)
            # 补零处理
            if month < 10:
                month = '0' + str(month)
            if day < 10:
                day = '0' + str(day)
            # 拼接
            card = str(code['code']) + str(year) + str(month) + str(day) + str(other) + str(sex['sex'])
            # 计算校验码
            card = str(card)+str((12-(sum([(int(str(card[NUM]))*(2**(17-NUM)) % 11) for NUM in range(17)]) % 11)) % 11).replace('10', 'X')
            # 返回内容
            data = {
                "idCard": card,
                "code": code['code'],
                'birthday': str(year) + '-' + str(month) + '-' + str(day),
                'sex': sex['type'],
                'province': code['provinceName'],
                'city': code['cityName'],
                'district': code['districtName']
            }
            return self.writeJson(200, data, '请求成功')
        else:
            return self.notFound()

port = 8809
httpd = HTTPServer(('', port), MyHttpHandler)
print("Server started on 0.0.0.0,port "+str(port)+".....")
httpd.serve_forever()
