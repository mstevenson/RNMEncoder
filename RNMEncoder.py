#!/usr/bin/env python

import sys
import array
import OpenEXR
import Imath

def main():
	xImg = OpenEXR.InputFile('images/x.exr')
	xNegImg = OpenEXR.InputFile('images/-x.exr')
	yImg = OpenEXR.InputFile('images/y.exr')
	yNegImg = OpenEXR.InputFile('images/-y.exr')
	zImg = OpenEXR.InputFile('images/z.exr')
	zNegImg = OpenEXR.InputFile('images/-z.exr')
	
	x = colors(xImg)
	xNeg = colors(xNegImg)
	y = colors(yImg)
	yNeg = colors(yNegImg)
	z = colors(zImg)
	zNeg = colors(zNegImg)
	
	# Compute the size
	dw = xImg.header()['dataWindow']
	size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
	
	# create 3 images with negative values
	subtract_negative_values(x, xNeg)
	subtract_negative_values(y, yNeg)
	subtract_negative_values(z, zNeg)
		
	make_rnm_non_negative (x, y, z)
	
	save(x, size)
	

def subtract_negative_values(colors_positive, colors_negative):
	for index in range(0, len(colors_positive.r) - 1):
		colors_positive.r[index] -= colors_negative.r[index]
		colors_positive.g[index] -= colors_negative.g[index]
		colors_positive.b[index] -= colors_negative.b[index]
		

def make_rnm_non_negative(colorsX, colorsY, colorsZ):
	accumulate_into_next_rnm (colorsX, colorsY)
	accumulate_into_next_rnm (colorsY, colorsZ)
	accumulate_into_next_rnm (colorsZ, colorsX)
	
def accumulate_into_next_rnm(colors_current, colors_next):
	for index in range(0, len(colors_current.r) - 1):
		desaturated = desaturate_light(colors_current.r[index], colors_current.g[index], colors_current.b[index])
		if desaturated < 0:
			colors_next.r[index] += colors_current.r[index]
			colors_next.g[index] += colors_current.g[index]
			colors_next.b[index] += colors_current.b[index]
	
def desaturate_light (r, g, b):
	return (r * 0.22) + (g * 0.707) + (b * 0.071)

# def convert_rnm_to_directional(x, y, z):
# 	dot_rnm_basis_normal_straight_up = 0.5773503
# 	one_over_three_times_dot_rnm_bassi_is_normal_straight_up = 1 / (3 * dot_rnm_basis_normal_straight_up)
# 	k_rgbm_max_range = 8
# 	max_rgbm_precision_over_two = 1 / (256 * k_rgbm_max_range * 2)
	


class colors:
	def __init__(self, image):
		(self.r, self.g, self.b) = self.get_rgb(image)
		
	def get_rgb(self, image):
		# Read the three color channels as 32-bit floats
		FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
		(R,G,B) = [array.array('f', image.channel(Chan, FLOAT)).tolist() for Chan in ("R", "G", "B") ]
		return (R,G,B)

def save(colors, size):
	# Convert to strings
	(Rs, Gs, Bs) = [ array.array('f', Chan).tostring() for Chan in (colors.r, colors.g, colors.b) ]
	
	# Write the three color channels to the output file
	out = OpenEXR.OutputFile("LightmapScale-0.exr", OpenEXR.Header(size[0], size[1]))
	out.writePixels({'R' : Rs, 'G' : Gs, 'B' : Gs })

if __name__ == "__main__":
	main();