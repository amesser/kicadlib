#!/usr/bin/python
# encoding: utf-8
#
# Altera FPGA Symbol pin helper script
# Copyright (C) 2017 Andreas Messer <andi@bastelmap.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

def altera_pinout_reader(fh):
  keys = []
  linebuf = ""

  for line in iter(fh):
    line = line.rstrip('\r\n\t')

    if line.startswith('Bank Number'):
      keys = line.split('\t')
    elif line.startswith('Notes'):
      keys = []
    elif keys:
      values = line.split('\t')

      if len(values) < len(keys):
        values.extend( [""] * (len(keys) - len(values)))

      yield dict(zip(keys,values))

with open(sys.argv[1],'rt') as fh:
  package = 'F484'

  pin_defs = list(x for x in altera_pinout_reader(fh) if package in x)

  banks = set(pin['Bank Number'] for pin in pin_defs)
  partno_by_bank = dict((x,i) for i, x in enumerate(sorted(banks)))

  y_offsets = dict( ((i,x),0) for i in partno_by_bank.values() for x in 'LR')
  x_offsets = dict( ((i,x),{'L': +400, 'R':-400}[x]) for i in partno_by_bank.values() for x in 'LR')
   
  for pin in pin_defs: 
    bank = pin['Bank Number']
    vref = pin['VREF']

    partno = partno_by_bank[bank]
    typ    = 'B'
    orient = 'L'

    pin_name = pin['Configuration Function']

    if not pin_name:
      pin_name = pin['Pin Name/Function']
    
      if pin_name == 'IO':
        pin_name = pin['Dedicated Tx/Rx Channel']

        if pin_name.startswith('DIFFIO_'):
          pin_name = pin_name[7:]

        pin_opt = pin['Optional Function(s)'].strip('"')

        if pin_opt:
          pin_name = '/'.join([pin_name] + pin_opt.split(','))
      elif pin_name == 'NC':
        typ    = 'N'
      elif pin_name == 'GND':
        typ    = 'W'
      elif pin_name.startswith('VCC'):
        typ    = 'W'
        orient = 'R'

      if pin_name.startswith('VCCIO'):
        partno = partno_by_bank[pin_name[5:]]
   
    ddr3_assign   = pin['HMC Pin Assignment for DDR3/DDR2 (2)']
    lpddr2_assign = pin['HMC Pin Assignment for LPDDR2']

    if ddr3_assign:
      pin_name = pin_name + "/" + ddr3_assign

    if lpddr2_assign:
      if lpddr2_assign != ddr3_assign:
        pin_name = pin_name + "/" + lpddr2_assign

    lst = ['X']
    lst.append(pin_name)
    lst.append(pin[package])
    lst.append('%d' % x_offsets[(partno, orient)])
    lst.append('%d' % y_offsets[(partno, orient)])
    lst.append('200') # length
    lst.append(orient)
    lst.append('50') # font size num
    lst.append('50') # font size name
    lst.append('%d' % (partno + 1))
    lst.append('1') # dmg
    lst.append(typ)

    y_offsets[(partno, orient)] -= 100
    print(" ".join(lst))
