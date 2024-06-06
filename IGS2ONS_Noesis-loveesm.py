#!/usr/bin/env python3
from PIL import Image, ImageEnhance
import concurrent.futures
import subprocess
import shutil
import glob
import sys
import os
import re


def img_resize_main(p, DIR_IMG):
	p_name = os.path.basename(p)
	p_r = os.path.join(DIR_IMG, p_name)

	im = Image.open(p)
	w = int(im.width * 600 / 768)
	h = int(im.height * 600 / 768)

	im_r = im.resize((w, h), Image.Resampling.LANCZOS)

	#画像個別処理
	if str(p_name).lower() == 'window_base.png':
		im_r.putalpha(192)

	elif str(p_name).lower() == 'load_base.png':
		enhancer = ImageEnhance.Brightness(im_r)
		im_r = enhancer.enhance(0.4)

	elif str(p_name).lower() == 'config_base.png':
		enhancer = ImageEnhance.Brightness(im_r)
		im_r = enhancer.enhance(0.2)

	elif str(p_name).lower() == 'view_cg.png':
		enhancer = ImageEnhance.Brightness(im_r)
		im_r = enhancer.enhance(0.2)

	im_r.save(p_r)


def img_resize(DIR_BG, DIR_FG, DIR_SYS, DIR_IMG):
	l = []
	l += glob.glob(os.path.join(DIR_BG, '*.png'))
	l += glob.glob(os.path.join(DIR_FG, '*.png'))
	l += glob.glob(os.path.join(DIR_SYS, '*.png'))

	os.makedirs(DIR_IMG, exist_ok=True)

	#本処理 - マルチスレッドで高速化
	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		for p in l: futures.append(executor.submit(img_resize_main, p, DIR_IMG))
		concurrent.futures.as_completed(futures)

	#クレジット結合
	im1 = Image.open(os.path.join(DIR_IMG, 'credit_01.png'))
	im2 = Image.open(os.path.join(DIR_IMG, 'credit_02.png'))
	im3 = Image.open(os.path.join(DIR_IMG, 'credit_03.png'))
	imnew = Image.new('RGBA', (im1.width, im1.height+im2.height+im3.height))
	imnew.paste(im1, (0, 0))
	imnew.paste(im2, (0, im1.height))
	imnew.paste(im3, (0, im1.height+im2.height))
	imnew.save(os.path.join(DIR_IMG, 'credit_join.png'))





def text_dec(DIR_SCR_DEC, DIR_SCR, EXE_IGS):
	os.makedirs(DIR_SCR_DEC, exist_ok=True)

	for p in glob.glob(os.path.join(DIR_SCR, '*.s')):
		n = (os.path.splitext(os.path.basename(p))[0])
		subprocess.run([EXE_IGS, '-p', p, n+'.txt'], shell=True, cwd=DIR_SCR)

	for p in glob.glob(os.path.join(DIR_SCR, '*.txt')):
		shutil.move(p, DIR_SCR_DEC)


def text_cnv(DEFAULT_TXT, DIR_SCR_DEC, ZERO_TXT):
	jmp_cnt = 0
	jmp_list = []

	with open(DEFAULT_TXT) as f:
		txt = f.read()

	for p in glob.glob(os.path.join(DIR_SCR_DEC, '*.txt')):
		with open(p, encoding='cp932', errors='ignore') as f:

			name = os.path.splitext(os.path.basename(p))[0]
			txt += '\nerrmsg:reset\n;--------------- '+ name +' ---------------\n*SCR_'+ name +'\n'
			OPJ_flag = False

			for line in f:
				goto_line = re.search(r'[0-9\s]+\s([0-9A-z-_]+?)\.s', line)
				txt_line = re.search(r'0400\s[A-z0-9]{4}\s(＃)?(.+?)\n', line)
				bg_line = re.search(r'(040F|0410)\s[0-9A-z]{4}\s(.+?)\.bmp', line)
				tatiset_line = re.search(r'0412\s[A-z0-9]{4}\s(.+?)\n', line)
				tatiload_line = re.search(r'0814 0000 01F4 0000', line)
				tatireset_line = re.search(r'0811 0000 0000 0000', line)
				wait_line = re.search(r'080E 0000 0BB8 0000', line)
				wait2_line = re.match(r'080E 0000 05DC 0000', line)
				black_line = re.search(r'0816 0001 0000 0000', line)
				bgmstop_line = re.search(r'0824 0000 03E8 0000', line)
				se_line = re.match(r'([A-z0-9_-]+?)\n', line)
				spmsg_line = re.match(r'049C\s0901\s(.+?)\.png', line)
				spmsg_end_line = re.match(r'0475 0001 043F', line)
				OPTIONJUMP_line = re.match(r'!OPTIONJUMP!', line)
				#txt_line = re.search(r'', line)

				if re.search('^\n', line):#空行
					pass#そのまま放置

				elif goto_line:
					line = 'goto *SCR_' + goto_line[1] + '\n'

				elif txt_line:

					if txt_line[1]:
						line = 'mov $10,"' + txt_line[2] + '"\n'

					else:
						msg = re.sub(r'\<(.+?)\<(.+?)\>', r'(\1/\2)', txt_line[2])
						line = msg + '\\\n'

				elif bg_line:
					line = 'vsp 9,0:vsp 8,0:print 1:bg "image\\' + bg_line[2] + '.png",10\n'

				elif tatiset_line:
					line = 'tati_set "' + tatiset_line[1] + '","' + tatiset_line[1][:3] + '"\n'

				elif tatiload_line:
					line = 'tati_load\n'

				elif tatireset_line:
					line = 'tati_reset\n'

				elif wait_line:
					line = 'wait 2000\n'

				elif wait2_line:
					line = 'wait 2000\n'

				elif black_line:
					line = 'vsp 9,0:vsp 8,0:print 1:bg black,10\n'

				elif bgmstop_line:
					line = 'bgmstop\n'

				elif se_line:
					line = 'def_SEset "' + se_line[1] + '"\n'

				elif spmsg_line:
					line = 'spmsg "' + spmsg_line[1] + '"\n'

				elif spmsg_end_line:
					line = 'spmsg_end\n'

				elif OPTIONJUMP_line:
					OPJ_flag = True

					jmp_cnt += 1
					line = r';JMP_CNT' + str(jmp_cnt) + '_\n'
				
				elif OPJ_flag:
					OPJ_flag = False
					jmp_list.append(line[:-1])
					line = r';' + line#エラー防止の為コメントアウト

				else:
					line = '\n'
					#line = r';' + line#エラー防止の為コメントアウト

				txt += line

			txt += '\n;SCR_'+ name +'_END'

	#-----ガ バ ガ バ 修 正-----
	#OP
	txt = txt.replace(r'goto *SCR_0020', 'mpegplay "video\\op.mpg",1\ngoto *SCR_0020')
	#選択肢1
	txt = txt.replace(r';JMP_CNT1_', r'select "'+jmp_list[0]+r'",*S1A,"'+jmp_list[1]+r'",*S1B')
	txt = txt.replace(r'がっちりと腰', r'*S1A'+'\nがっちりと腰')
	txt = txt.replace(r'慌てて引', r'goto *S1END'+'\n*S1B\n慌てて引')
	txt = txt.replace('微かだった。\\', '微かだった。\\\n*S1END\n')
	#選択肢2
	txt = txt.replace(r';JMP_CNT3_', r'select "'+jmp_list[2]+r'",*S2A,"'+jmp_list[3]+r'",*S2B'+'\n*S2A')
	txt = txt.replace(r'引き抜いた―', 'goto *S2END\n*S2B\n引き抜いた―')
	txt = txt.replace(r'「……あやか、よ', '*S2END\n「……あやか、よ')
	#選択肢3
	txt = txt.replace(r';JMP_CNT5_', 'mov $60,""')
	txt = txt.replace(r';JMP_CNT6_', 'if %200==1 if %201==1 mov $60,"'+jmp_list[6]+'"')
	txt = txt.replace(r';JMP_CNT7_', r'select "'+jmp_list[4]+r'",*S3A,"'+jmp_list[5]+r'",*S3B,$60,*S3C'+'\n*S3A\nmov %100,1')
	txt = txt.replace(r'……どち', 'goto *S3END\n*S3B\nmov %100,2\n……どち')
	txt = txt.replace(r'……ダメだ。', 'goto *S3END\n*S3C\nmov %100,3\n……ダメだ。')
	txt = txt.replace('でいないと。\\', 'でいないと。\\\n*S3END\n')
	txt = txt.replace(r'goto *SCR_A0230', r'if %100==1 goto *SCR_A0230')
	txt = txt.replace(r'goto *SCR_B0450', r'if %100==2 goto *SCR_B0450')
	txt = txt.replace(r'goto *SCR_C0690', r'if %100==3 goto *SCR_C0690')
	#選択肢4
	txt = txt.replace(r';JMP_CNT8_', r'select "'+jmp_list[7]+r'",*S4A,"'+jmp_list[8]+r'",*S4B'+'\n*S4A')
	txt = txt.replace(r'正直、ち', '*S4B\n正直、ち')
	#選択肢5
	txt = txt.replace(r';JMP_CNT10_', r'select "'+jmp_list[9]+r'",*S5A,"'+jmp_list[10]+r'",*S5B'+'\n*S5A')
	txt = txt.replace('深く息をついた。\\', '深く息をついた。\\\ngoto *S5END\n*S5B')
	txt = txt.replace('体を擦り寄らせた。\\', '体を擦り寄らせた。\\\n*S5END')
	txt = txt.replace(r';SCR_a0650z_END', 'bgmstop:dwavestop -1:csp -1:reset')
	#選択肢6
	txt = txt.replace(r';JMP_CNT12_', r'select "'+jmp_list[11]+r'",*S6A,"'+jmp_list[12]+r'",*S6B'+'\n*S6B')
	txt = txt.replace(r'goto *SCR_A0420', 'goto *SCR_A0420\n*S6A')
	txt = txt.replace(r';SCR_A0660_END', 'bgmstop:dwavestop -1:csp -1:reset')
	txt = txt.replace(r';SCR_A0440Z_END', 'bgmstop:dwavestop -1:skipoff:mov %200,1:bgmonce "bgm\\Led_a.ogg":bg "image\\ed1_ayaka.png",10:mov %150,93066:gosub *staffroll:click:bgmstop:dwavestop -1:csp -1:reset')#ED1
	#選択肢7
	txt = txt.replace(r';JMP_CNT14_', r'select "'+jmp_list[13]+r'",*S7A,"'+jmp_list[14]+r'",*S7B'+'\n*S7A')
	txt = txt.replace(r'goto *SCR_B0540A', 'goto *SCR_B0540A\n*S7B')
	txt = txt.replace(r';SCR_B0670_END', 'bgmstop:dwavestop -1:csp -1:reset')
	#選択肢8
	txt = txt.replace(r';JMP_CNT16_', r'select "'+jmp_list[15]+r'",*S8A,"'+jmp_list[16]+r'",*S8B'+'\n*S8B')
	txt = txt.replace(r'goto *SCR_B0630', 'goto *SCR_B0630\n*S8A')
	txt = txt.replace(r';SCR_b0680z_END', 'bgmstop:dwavestop -1:csp -1:reset')
	txt = txt.replace(r';SCR_B0640Z_END', 'bgmstop:dwavestop -1:skipoff:mov %201,1:bgmonce "bgm\\Led_a.ogg":bg "image\\ed2_ayaka.png",10:mov %150,93066:gosub *staffroll:click:bgmstop:dwavestop -1:csp -1:reset')#ED2
	#選択肢9
	txt = txt.replace(r';JMP_CNT18_', r'select "'+jmp_list[17]+r'",*S9A,"'+jmp_list[18]+r'",*S9B'+'\n*S9A\nmov %101,1')
	txt = txt.replace('の準備を始めた。\\', 'の準備を始めた。\\\ntati_reset')
	txt = txt.replace('るさを感じた。\\', 'るさを感じた。\\\ngoto *SCR_C0700Z\n*S9B\nmov %101,2')
	txt = txt.replace('着てもらう。\\', '着てもらう。\\\nif %101==2 goto *S9SKIP')
	txt = txt.replace('かは顔を見合わせ、それからにっこりと笑って言った。\\', 'かは顔を見合わせ、それからにっこりと笑って言った。\\\ngoto *S9END\n*S9SKIP')
	txt = txt.replace('華は顔を見合わせ、それからにっこりと笑って言った。\\', '華は顔を見合わせ、それからにっこりと笑って言った。\\\n*S9END')
	txt = txt.replace(';SCR_C0700Z_END', 'tati_reset:csp -1:bgmstop:dwavestop -1:skipoff:mov %202,1:bgmonce "bgm\\Led_s.ogg":bg "image\\ed3_harem.png",10:mov %150,126007:gosub *staffroll:click:bgmstop:dwavestop -1:csp -1:reset')#ED3

	open(ZERO_TXT, 'w', errors='ignore').write(txt)


def file_check(EXE_IGS, DEFAULT_TXT, DIR_SCR, DIR_BG, DIR_FG, DIR_SYS):
	c = True
	for p in [EXE_IGS, DEFAULT_TXT, DIR_SCR, DIR_BG, DIR_FG, DIR_SYS]:
		if not os.path.exists(p):
			print(p+ ' is not found!')
			c = False
	
	return c


def junk_del(DIR_BG, DIR_FG, DIR_SYS, DIR_SCR, DIR_SCR_DEC, DEFAULT_TXT, debug):
	shutil.rmtree(DIR_BG)
	shutil.rmtree(DIR_FG)
	shutil.rmtree(DIR_SYS)
	shutil.rmtree(DIR_SCR)
	shutil.rmtree(DIR_SCR_DEC)
	if not debug: os.remove(DEFAULT_TXT)


def main():

	#デバッグ
	debug = 0

	same_hierarchy = (os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
	EXE_IGS = os.path.join(same_hierarchy,'igscriptD.exe')
	DEFAULT_TXT = os.path.join(same_hierarchy,'default.txt')

	if debug: same_hierarchy = os.path.join(same_hierarchy,'Gungnir_loveesm_EXT')#debug
	ZERO_TXT = os.path.join(same_hierarchy,'0.txt')
	DIR_SCR = os.path.join(same_hierarchy,'script')
	DIR_SCR_DEC = os.path.join(same_hierarchy,'script_dec')

	DIR_BG = os.path.join(same_hierarchy,'bgimage')
	DIR_FG = os.path.join(same_hierarchy,'fgimage')
	DIR_SYS = os.path.join(same_hierarchy,'system')
	DIR_IMG = os.path.join(same_hierarchy,'image')

	if file_check(EXE_IGS, DEFAULT_TXT, DIR_SCR, DIR_BG, DIR_FG, DIR_SYS):
		img_resize(DIR_BG, DIR_FG, DIR_SYS, DIR_IMG)
		text_dec(DIR_SCR_DEC, DIR_SCR, EXE_IGS)
		text_cnv(DEFAULT_TXT, DIR_SCR_DEC, ZERO_TXT)
		junk_del(DIR_BG, DIR_FG, DIR_SYS, DIR_SCR, DIR_SCR_DEC, DEFAULT_TXT, debug)


main()