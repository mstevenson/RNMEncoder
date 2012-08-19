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
	
	x = Colors.from_image(xImg)
	xNeg = Colors.from_image(xNegImg)
	y = Colors.from_image(yImg)
	yNeg = Colors.from_image(yNegImg)
	z = Colors.from_image(zImg)
	zNeg = Colors.from_image(zNegImg)
	
	# Compute the size
	dw = xImg.header()['dataWindow']
	size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
	
	# create 3 images with negative values
	subtract_negative_values(x, xNeg)
	subtract_negative_values(y, yNeg)
	subtract_negative_values(z, zNeg)
		
	make_rnm_non_negative (x, y, z)
	
	# write directional lightmap into x
	finalColors = convert_rnm_to_directional(x, y, z)
	
	Save(finalColors, size)
	

def subtract_negative_values(colors_positive, colors_negative):
	for index in range(0, len(colors_positive.r)):
		colors_positive.r[index] -= colors_negative.r[index]
		colors_positive.g[index] -= colors_negative.g[index]
		colors_positive.b[index] -= colors_negative.b[index]
		

def make_rnm_non_negative(colorsX, colorsY, colorsZ):
	accumulate_into_next_rnm (colorsX, colorsY)
	accumulate_into_next_rnm (colorsY, colorsZ)
	accumulate_into_next_rnm (colorsZ, colorsX)
	
def accumulate_into_next_rnm(colors_current, colors_next):
	for index in range(0, len(colors_current.r)):
		desaturated = desaturate_light(colors_current.r[index], colors_current.g[index], colors_current.b[index])
		if desaturated < 0:
			colors_next.r[index] += colors_current.r[index]
			colors_next.g[index] += colors_current.g[index]
			colors_next.b[index] += colors_current.b[index]
			
			colors_current.r[index] = 0;
			colors_current.g[index] = 0;
			colors_current.b[index] = 0;
	
def desaturate_light (r, g, b):
	return (r * 0.22) + (g * 0.707) + (b * 0.071)

# returns directional lightmap Color data object
def convert_rnm_to_directional(colorsX, colorsY, colorsZ):
	# previous name:  dot_rnm_basis_normal_straight_up
	normal = 0.5773503
	one_over_three_times_dot_rnm_basis_is_normal_straight_up = 1 / (3 * normal)
	k_rgbm_max_range = 8
	# previous name:  max_rgbm_precision_over_two
	max_precision = 1 / (256 * k_rgbm_max_range * 2)
	
	directional = Colors();
	directional.r = colorsX.r
	directional.g = colorsY.r
	directional.b = colorsZ.r
	
	for index in range(0, len(colorsX.r)):
		light0 = (colorsX.r[index], colorsX.g[index], colorsX.b[index])
		light1 = (colorsY.r[index], colorsY.g[index], colorsY.b[index])
		light2 = (colorsZ.r[index], colorsZ.g[index], colorsZ.b[index])
		
		averageLight0 = [normal * c for c in light0]
		averageLight1 = [normal * c for c in light1]
		averageLight2 = [normal * c for c in light2]
		
		averageLightVec = ((averageLight0[0] + averageLight1[0] + averageLight2[0]), (averageLight0[1] + averageLight1[1] + averageLight2[1]), (averageLight0[2] + averageLight1[2] + averageLight2[2]))
		desaturatedAverageLight = desaturate_light(averageLightVec[0], averageLightVec[1], averageLightVec[2])
		
		if averageLightVec[0] < max_precision and averageLightVec[1] < max_precision and averageLightVec[2] < max_precision:
			scale0 = scale1 = scale2 = one_over_three_times_dot_rnm_basis_is_normal_straight_up
		else:
			one_over_scale_average = one_over_three_times_dot_rnm_basis_is_normal_straight_up
			scale0 = desaturate_light(light0[0], light0[1], light0[2]) * one_over_scale_average
			scale1 = desaturate_light(light1[0], light1[1], light1[2]) * one_over_scale_average
			scale2 = desaturate_light(light2[0], light2[1], light2[2]) * one_over_scale_average
			
		directional.r[index] = scale0
		directional.g[index] = scale1
		directional.b[index] = scale2
	
	return directional
	


class Colors:
	def __init__(self):
		self.r = []
		self.g = []
		self.b = []
	@classmethod
	def from_image (self, image):
		c = Colors()
		(c.r, c.g, c.b) = c.get_rgb(image)
		return c
	@classmethod
	def from_rgb (self, r, g, b):
		c = Colors()
		c.r = r
		c.g = g
		c.b = b
		return c
		
	def get_rgb(self, image):
		# Read the three color channels as 32-bit floats
		FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
		(R,G,B) = [array.array('f', image.channel(Chan, FLOAT)).tolist() for Chan in ("R", "G", "B") ]
		return (R,G,B)

def Save(colors, size):
	# Convert to strings
	(Rs, Gs, Bs) = [ array.array('f', Chan).tostring() for Chan in (colors.r, colors.g, colors.b) ]
	
	# Write the three color channels to the output file
	out = OpenEXR.OutputFile("LightmapScale-0.exr", OpenEXR.Header(size[0], size[1]))
	out.writePixels({'R' : Rs, 'G' : Gs, 'B' : Bs })

if __name__ == "__main__":
	main();