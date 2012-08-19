#!/usr/bin/env python

import sys
import array
import OpenEXR
import Imath

class Vector3:
	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z
	def __add__(self, other):
		return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
	def __mul__(self, scaler):
		return Vector3(self.x * scaler, self.y * scaler, self.z * scaler)
	def zero(self):
		return Vector3(0, 0, 0)

class Colors:
	def __init__(self):
		self.r = []
		self.g = []
		self.b = []
		
	@classmethod
	def from_image (self, exr_image):
		FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
		c = Colors()
		(c.r,c.g,c.b) = [array.array('f', exr_image.channel(Channel, FLOAT)).tolist() for Channel in ("R", "G", "B") ]
		return c
		
	@classmethod
	def from_rgb (self, r, g, b):
		c = Colors()
		(c.r,c.g,c.b) = (r,g,b)
		return c


def main():
	if len(sys.argv) != 3:
	    print "usage: RNMEncoder.py input-folder output-name"
	    sys.exit(1)
	
	input_folder = sys.argv[1]
	out_name = sys.argv[2]
	
	xImg = OpenEXR.InputFile(input_folder + '/x.exr')
	
	x = Colors.from_image( xImg )
	xNeg = Colors.from_image( OpenEXR.InputFile(input_folder + '/-x.exr') )
	y = Colors.from_image( OpenEXR.InputFile(input_folder + '/y.exr') )
	yNeg = Colors.from_image( OpenEXR.InputFile(input_folder + '/-y.exr') )
	z = Colors.from_image( OpenEXR.InputFile(input_folder + '/z.exr') )
	zNeg = Colors.from_image( OpenEXR.InputFile(input_folder + '/-z.exr') )
	
	# calculate the image dimensions
	dw = xImg.header()['dataWindow']
	size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
	
	# create 3 images with negative values
	subtract_negative_values(x, xNeg)
	subtract_negative_values(y, yNeg)
	subtract_negative_values(z, zNeg)
	
	make_rnm_non_negative (x, y, z)
	
	# write directional lightmap into x
	finalColors = convert_rnm_to_directional(x, y, z)
	
	save(finalColors, out_name, size)


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
	for (cr, cg, cb, nr, ng, nb) in zip(colors_current.r, colors_current.g, colors_current.b, colors_next.r, colors_next.g, colors_next.b):
		current = Vector3(cr, cg, cb)
		next = Vector3(nr, ng, nb)
		desaturated = desaturate_light(current)
		if desaturated < 0:
			next = next + current
			current = Vector3.zero
	
	
def desaturate_light (rgb_vector):
	return (rgb_vector.x * 0.22) + (rgb_vector.y * 0.707) + (rgb_vector.z * 0.071)


# returns directional lightmap Color data object
def convert_rnm_to_directional(colorsX, colorsY, colorsZ):
	dot_rnm_basis_normal_straight_up = 0.5773503
	one_over_three_times_dot_rnm_basis_is_normal_straight_up = 1 / (3 * dot_rnm_basis_normal_straight_up)
	k_rgbm_max_range = 8
	max_rgbm_precision_over_two = 1 / (256 * k_rgbm_max_range * 2)
	
	directional = Colors();
	
	for (xr, xg, xb, yr, yg, yb, zr, zg, zb) in zip(colorsX.r, colorsX.g, colorsX.b, colorsY.r, colorsY.g, colorsY.b, colorsZ.r, colorsZ.g, colorsZ.b):
		light0 = Vector3(xr, xg, xb)
		light1 = Vector3(yr, yg, yb)
		light2 = Vector3(zr, zg, zb)
		
		average_light = (light0 * dot_rnm_basis_normal_straight_up) + (light1 * dot_rnm_basis_normal_straight_up) + (light2 * dot_rnm_basis_normal_straight_up)
		
		desaturated_average_light = desaturate_light(average_light)
		
		if average_light.x < max_rgbm_precision_over_two and average_light.y < max_rgbm_precision_over_two and average_light.z < max_rgbm_precision_over_two:
			scale0 = scale1 = scale2 = one_over_three_times_dot_rnm_basis_is_normal_straight_up
		else:
			one_over_scale_average = 1 / desaturated_average_light
			scale0 = desaturate_light(light0) * one_over_scale_average
			scale1 = desaturate_light(light1) * one_over_scale_average
			scale2 = desaturate_light(light2) * one_over_scale_average
			
		directional.r.append(scale0)
		directional.g.append(scale1)
		directional.b.append(scale2)
	
	return directional
	

def pixel_list_from_image(exr_image):
	FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
	(Rs,Gs,Bs) = [array.array('f', exr_image.channel(Channel, FLOAT)).tolist() for Channel in ("R", "G", "B") ]
	return [Pixel(r,g,b) for r,g,b in zip(Rs,Gs,Bs)]


def save(colors, name, size):
	# Convert to strings
	(Rs, Gs, Bs) = [ array.array('f', Chan).tostring() for Chan in (colors.r, colors.g, colors.b) ]
	
	# Write the three color channels to the output file
	out = OpenEXR.OutputFile(name + ".exr", OpenEXR.Header(size[0], size[1]))
	out.writePixels({'R' : Rs, 'G' : Gs, 'B' : Bs })


if __name__ == "__main__":
	main();