#!/usr/bin/env python3
from math import pi, sin, cos, atan2, radians, degrees
from random import randint
import pygame as pg
import numpy as np

FLLSCRN = False       # True untuk Fullscreen, atau False untuk Window
JUMLAH_SEMUT = 42     # Jumlah Semut yang akan di-spawn
LEBAR = 1200          # default 1200
TINGGI = 800          # default 800
FPS = 60              # 48-90
VSYNC = True          # batasi frame rate ke refresh rate
PRATIO = 5            # Ukuran Pixel untuk grid Pheromone, 5 adalah yang terbaik
TAMPILFPS = True      # tampilkan debug framerate

class Semut(pg.sprite.Sprite):
    def __init__(self, drawSurf, sarang, pheroLayer):
        super().__init__()
        self.drawSurf = drawSurf
        self.curW, self.curH = self.drawSurf.get_size()
        self.pgSize = (int(self.curW/PRATIO), int(self.curH/PRATIO))
        self.isMyTrail = np.full(self.pgSize, False)
        self.phero = pheroLayer
        self.sarang = sarang
        self.image = pg.Surface((12, 21)).convert()
        self.image.set_colorkey(0)
        cBrown = (100,42,42)
        # Gambar Semut
        pg.draw.aaline(self.image, cBrown, [0, 5], [11, 15])
        pg.draw.aaline(self.image, cBrown, [0, 15], [11, 5]) # kaki
        pg.draw.aaline(self.image, cBrown, [0, 10], [12, 10])
        pg.draw.aaline(self.image, cBrown, [2, 0], [4, 3]) # antena kiri
        pg.draw.aaline(self.image, cBrown, [9, 0], [7, 3]) # antena kanan
        pg.draw.ellipse(self.image, cBrown, [3, 2, 6, 6]) # kepala
        pg.draw.ellipse(self.image, cBrown, [4, 6, 4, 9]) # badan
        pg.draw.ellipse(self.image, cBrown, [3, 13, 6, 8]) # bokong
        # simpan gambar untuk nanti
        self.orig_img = pg.transform.rotate(self.image.copy(), -90)
        self.rect = self.image.get_rect(center=self.sarang)
        self.ang = randint(0, 360)
        self.desireDir = pg.Vector2(cos(radians(self.ang)),sin(radians(self.ang)))
        self.pos = pg.Vector2(self.rect.center)
        self.vel = pg.Vector2(0,0)
        self.last_sdp = (sarang[0]/10/2,sarang[1]/10/2)
        self.mode = 0

    def update(self, dt):  # perilaku
        mid_result = left_result = right_result = [0,0,0]
        mid_GA_result = left_GA_result = right_GA_result = [0,0,0]
        randAng = randint(0,360)
        accel = pg.Vector2(0,0)
        warnaMakanan = (20,150,2)  # warna makanan yang dicari
        wandrStr = .12  # seberapa acak mereka berjalan
        maxSpeed = 12  # 10-12 
        steerStr = 3  # 3 atau 4
        # Mengubah koordinat layar semut saat ini, ke resolusi yang lebih kecil dari pherogrid.
        scaledown_pos = (int(self.pos.x/PRATIO), int(self.pos.y/PRATIO))
        # Dapatkan lokasi untuk diperiksa sebagai titik sensor, dalam pasangan untuk deteksi yang lebih baik.
        mid_sens = Vec2.vint(self.pos + pg.Vector2(20, 0).rotate(self.ang))
        left_sens = Vec2.vint(self.pos + pg.Vector2(18, -8).rotate(self.ang)) # -9
        right_sens = Vec2.vint(self.pos + pg.Vector2(18, 8).rotate(self.ang)) # 9

        if self.drawSurf.get_rect().collidepoint(mid_sens):
            mspos = (mid_sens[0]//PRATIO,mid_sens[1]//PRATIO)
            mid_result = self.phero.img_array[mspos]
            mid_isID = self.isMyTrail[mspos]
            mid_GA_result = self.drawSurf.get_at(mid_sens)[:3]
        if self.drawSurf.get_rect().collidepoint(left_sens):
            left_result, left_isID, left_GA_result = self.sensCheck(left_sens)
        if self.drawSurf.get_rect().collidepoint(right_sens):
            right_result, right_isID, right_GA_result = self.sensCheck(right_sens)

        if self.mode == 0 and self.pos.distance_to(self.sarang) > 21:
            self.mode = 1

        elif self.mode == 1:  # Cari makanan, atau jejak ke makanan.
            setAcolor = (0,0,100)
            if scaledown_pos != self.last_sdp and scaledown_pos[0] in range(0,self.pgSize[0]) and scaledown_pos[1] in range(0,self.pgSize[1]):
                self.phero.img_array[scaledown_pos] += setAcolor
                self.isMyTrail[scaledown_pos] = True
                self.last_sdp = scaledown_pos
            if mid_result[1] > max(left_result[1], right_result[1]):
                self.desireDir += pg.Vector2(1,0).rotate(self.ang).normalize()
                wandrStr = .1
            elif left_result[1] > right_result[1]:
                self.desireDir += pg.Vector2(1,-2).rotate(self.ang).normalize() #kiri (0,-1)
                wandrStr = .1
            elif right_result[1] > left_result[1]:
                self.desireDir += pg.Vector2(1,2).rotate(self.ang).normalize() #kanan (0, 1)
                wandrStr = .1
            if left_GA_result == warnaMakanan and right_GA_result != warnaMakanan :
                self.desireDir += pg.Vector2(0,-1).rotate(self.ang).normalize() #kiri (0,-1)
                wandrStr = .1
            elif right_GA_result == warnaMakanan and left_GA_result != warnaMakanan:
                self.desireDir += pg.Vector2(0,1).rotate(self.ang).normalize() #kanan (0, 1)
                wandrStr = .1
            elif mid_GA_result == warnaMakanan: # jika makanan
                self.desireDir = pg.Vector2(-1,0).rotate(self.ang).normalize()
                wandrStr = .01
                steerStr = 5
                self.mode = 2

        elif self.mode == 2:  # Setelah menemukan makanan, ikuti jejak sendiri kembali ke sarang, atau menuju arah umum sarang.
            setAcolor = (0,80,0)
            if scaledown_pos != self.last_sdp and scaledown_pos[0] in range(0,self.pgSize[0]) and scaledown_pos[1] in range(0,self.pgSize[1]):
                self.phero.img_array[scaledown_pos] += setAcolor
                self.last_sdp = scaledown_pos
            if self.pos.distance_to(self.sarang) < 24:
                self.desireDir = pg.Vector2(-1,0).rotate(self.ang).normalize()
                self.isMyTrail[:] = False
                maxSpeed = 5
                wandrStr = .01
                steerStr = 5
                self.mode = 1
            elif mid_result[2] > max(left_result[2], right_result[2]) and mid_isID:
                self.desireDir += pg.Vector2(1,0).rotate(self.ang).normalize()
                wandrStr = .1
            elif left_result[2] > right_result[2] and left_isID:
                self.desireDir += pg.Vector2(1,-2).rotate(self.ang).normalize() #kiri (0,-1)
                wandrStr = .1
            elif right_result[2] > left_result[2] and right_isID:
                self.desireDir += pg.Vector2(1,2).rotate(self.ang).normalize() #kanan (0, 1)
                wandrStr = .1
            else:  # mungkin pertama tambahkan ELSE IKUTI JEJAK LAIN?
                self.desireDir += pg.Vector2(self.sarang - self.pos).normalize() * .08
                wandrStr = .1 

        warnaDinding = (50,50,50)  # hindari dinding dengan warna ini
        if left_GA_result == warnaDinding:
            self.desireDir += pg.Vector2(0,2).rotate(self.ang) #.normalize()
            wandrStr = .1
            steerStr = 7
        elif right_GA_result == warnaDinding:
            self.desireDir += pg.Vector2(0,-2).rotate(self.ang) #.normalize()
            wandrStr = .1
            steerStr = 7
        elif mid_GA_result == warnaDinding:
            self.desireDir = pg.Vector2(-2,0).rotate(self.ang) #.normalize()
            maxSpeed = 4
            wandrStr = .1
            steerStr = 7

        # Hindari tepi
        if not self.drawSurf.get_rect().collidepoint(left_sens) and self.drawSurf.get_rect().collidepoint(right_sens):
            self.desireDir += pg.Vector2(0,1).rotate(self.ang) #.normalize()
            wandrStr = .01
            steerStr = 5
        elif not self.drawSurf.get_rect().collidepoint(right_sens) and self.drawSurf.get_rect().collidepoint(left_sens):
            self.desireDir += pg.Vector2(0,-1).rotate(self.ang) #.normalize()
            wandrStr = .01
            steerStr = 5
        elif not self.drawSurf.get_rect().collidepoint(Vec2.vint(self.pos + pg.Vector2(21, 0).rotate(self.ang))):
            self.desireDir += pg.Vector2(-1,0).rotate(self.ang) #.normalize()
            maxSpeed = 5
            wandrStr = .01
            steerStr = 5

        randDir = pg.Vector2(cos(radians(randAng)),sin(radians(randAng)))
        self.desireDir = pg.Vector2(self.desireDir + randDir * wandrStr).normalize()
        dzVel = self.desireDir * maxSpeed
        dzStrFrc = (dzVel - self.vel) * steerStr
        accel = dzStrFrc if pg.Vector2(dzStrFrc).magnitude() <= steerStr else pg.Vector2(dzStrFrc.normalize() * steerStr)
        velo = self.vel + accel * dt
        self.vel = velo if pg.Vector2(velo).magnitude() <= maxSpeed else pg.Vector2(velo.normalize() * maxSpeed)
        self.pos += self.vel * dt
        self.ang = degrees(atan2(self.vel[1],self.vel[0]))
        # sesuaikan sudut gambar agar sesuai dengan arah
        self.image = pg.transform.rotate(self.orig_img, -self.ang)
        self.rect = self.image.get_rect(center=self.rect.center)  # perbaikan penempatan tengah
        # perbarui posisi sebenarnya
        self.rect.center = self.pos

    def sensCheck(self, pos): #, pos2): # periksa titik yang diberikan dalam Array, ID, dan piksel di layar.
        sdpos = (int(pos[0]/PRATIO),int(pos[1]/PRATIO))
        array_r = self.phero.img_array[sdpos]
        ga_r = self.drawSurf.get_at(pos)[:3]
        return array_r, self.isMyTrail[sdpos], ga_r

class PheroGrid():
    def __init__(self, ukuranBesar):
        self.surfSize = (int(ukuranBesar[0]/PRATIO), int(ukuranBesar[1]/PRATIO))
        self.image = pg.Surface(self.surfSize).convert()
        self.img_array = np.array(pg.surfarray.array3d(self.image),dtype=float)
    def update(self, dt):
        self.img_array -= .2 * (60/FPS) * ((dt/10) * FPS)
        self.img_array = self.img_array.clip(0,255)
        pg.surfarray.blit_array(self.image, self.img_array)
        return self.image

class Makanan(pg.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pos
        self.image = pg.Surface((16, 16))
        self.image.fill(0)
        self.image.set_colorkey(0)
        pg.draw.circle(self.image, [20,150,2], [8, 8], 4)
        self.rect = self.image.get_rect(center=pos)
    def pickup(self):
        self.kill()

class Vec2():
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y
	def vint(self):
		return (int(self.x), int(self.y))

def main():
    pg.init()  # siapkan window
    pg.display.set_caption("NAnts")
    try: pg.display.set_icon(pg.img.load("nants.png"))
    except: print("FYI: nants.png icon tidak ditemukan, melewati..")

    if FLLSCRN:
        currentRez = (pg.display.Info().current_w, pg.display.Info().current_h)
        screen = pg.display.set_mode(currentRez, pg.SCALED | pg.NOFRAME | pg.FULLSCREEN, vsync=VSYNC)
    else: screen = pg.display.set_mode((LEBAR, TINGGI), pg.SCALED, vsync=VSYNC)

    cur_w, cur_h = screen.get_size()
    ukuranLayar = (cur_w, cur_h)
    sarang = (cur_w/3, cur_h/2)

    pekerja = pg.sprite.Group()
    pheroLayer = PheroGrid(ukuranLayar)

    for n in range(JUMLAH_SEMUT):
        pekerja.add(Semut(screen, sarang, pheroLayer))

    daftarMakanan = []
    makanan = pg.sprite.Group()
    font = pg.font.Font(None, 30)
    clock = pg.time.Clock()
    fpsChecker = 0
    # loop utama
    while True:
        for e in pg.event.get():
            if e.type == pg.QUIT or e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                return
            elif e.type == pg.MOUSEBUTTONDOWN:
                mousepos = pg.mouse.get_pos()
                if e.button == 1:
                    foodBits = 200
                    fRadius = 50
                    for i in range(0, foodBits): # spawn bit makanan secara merata dalam lingkaran
                        dist = pow(i / (foodBits - 1.0), 0.5) * fRadius
                        angle = 2 * pi * 0.618033 * i
                        fx = mousepos[0] + dist * cos(angle)
                        fy = mousepos[1] + dist * sin(angle)
                        makanan.add(Makanan((fx,fy)))
                    daftarMakanan.extend(makanan.sprites())
                if e.button == 3:
                    for fbit in daftarMakanan:
                        if pg.Vector2(mousepos).distance_to(fbit.rect.center) < fRadius+5:
                            fbit.pickup()
                    daftarMakanan = makanan.sprites()

        dt = clock.tick(FPS) / 100

        pheroImg = pheroLayer.update(dt)
        pheroLayer.img_array[170:182,0:80] = (50,50,50)  # dinding

        pekerja.update(dt)

        screen.fill(0) # isi HARUS setelah sensor diperbarui, agar gambar sebelumnya terlihat oleh mereka

        rescaled_img = pg.transform.scale(pheroImg, (cur_w, cur_h))
        pg.Surface.blit(screen, rescaled_img, (0,0))

        #pekerja.update(dt)  # aktifkan di sini untuk melihat titik debug
        makanan.draw(screen)

        pg.draw.circle(screen, [40,10,10], (sarang[0],sarang[1]+6), 6, 3)
        pg.draw.circle(screen, [50,20,20], (sarang[0],sarang[1]+4), 9, 4)
        pg.draw.circle(screen, [60,30,30], (sarang[0],sarang[1]+2), 12, 4)
        pg.draw.circle(screen, [70,40,40], sarang, 16, 5)

        #pg.draw.rect(screen, (50,50,50), [900, 0, 50, 500]) # dinding uji

        pekerja.draw(screen)

        if TAMPILFPS : screen.blit(font.render(str(int(clock.get_fps())), True, [0,200,0]), (8, 8))

        pg.display.update()


if __name__ == '__main__':
    main()
    pg.quit()
