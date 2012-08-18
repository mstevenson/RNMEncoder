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
	
	print x.r[0]

	# # Normalize so that brightest sample is 1
	# brightest = max(R + G + B)
	# R = [ i / brightest for i in R ]
	# G = [ i / brightest for i in G ]
	# B = [ i / brightest for i in B ]
	# 
	# # Convert to strings
	# (Rs, Gs, Bs) = [ array.array('f', Chan).tostring() for Chan in (R, G, B) ]
	# 
	# # Write the three color channels to the output file
	# out = OpenEXR.OutputFile("LightmapScale-0.exr", OpenEXR.Header(sz[0], sz[1]))
	# out.writePixels({'R' : Rs, 'G' : Gs, 'B' : Gs })

class colors:
	def __init__(self, image):
		(self.r, self.g, self.b) = self.get_rgb(image)
		
	def get_rgb(self, image):
		# Read the three color channels as 32-bit floats
		FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
		(R,G,B) = [array.array('f', image.channel(Chan, FLOAT)).tolist() for Chan in ("R", "G", "B") ]
		return (R,G,B)


if __name__ == "__main__":
	main();