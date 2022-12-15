import re
import sys

# reformatting uProf_pcm csv data
def uprof_pcm_formatter(file, newfile):
    f = open(file,"r")
    f_new = open(newfile,"w")
    
    for line in f:
        # extract initial time
        if "Profile Time:" in line:
            full_date = line[14:-1]
            full_date = full_date.replace("/", "-")
            msec0 = int(full_date[20:23])
            sec0  = int(full_date[17:19])
            min0  = int(full_date[14:16])
            hour0 = int(full_date[11:13])
            day0  = int(full_date[8:10])
        
        # append package numbers to headers,
        # and add headers for l2 cache hit ratio
        if "Package" in line:
            header1 = line.split(",")
        if "Timestamp" in line:
            header2 = line.split(",")[1:]

            package_num = "0"
            header_new = ["Timestamp"]
            for package,header in zip(header1,header2):
                if (package=="\n") or (header=="\n"):
                    header_new += ["L2 Hit Ratio PKG0", "L2 Hit Ratio PKG1", "\n"]
                    header_new_str = ",".join(header_new)
                    f_new.write(header_new_str)
                if "Package" in package:
                    package_num = package[-1]
                header_new += [header+" PKG" + package_num]
            
                
        # generate full timestamps,
        # and calculate L2 hit ratio
        if re.search("..:..:..:...,", line):
            msec_n_old = int(line[9:12])
            sec_n_old = int(line[6:8])
            min_n_old = int(line[3:5])
            hour_n_old = int(line[0:2])
            
            msec_n = (msec_n_old + msec0) % 1000
            msec_carryover = (msec_n_old + msec0) // 1000
            sec_n  = (sec_n_old + sec0 + msec_carryover) % 60
            sec_carryover  = (sec_n_old + sec0 + msec_carryover) // 60
            min_n  = (min_n_old + min0 + sec_carryover) % 60
            min_carryover = (min_n_old + min0 + sec_carryover) // 60
            hour_n = (hour_n_old + hour0 + min_carryover) % 24
            hour_carryover = (hour_n_old + hour0 + min_carryover) // 24
            day_n  = (day0 + hour_carryover)
            date_n = "{year_month}-{day:02d} {hour:02d}:{min:02d}:{sec:02d}".format(year_month=full_date[0:7], day=day_n, hour=hour_n, min=min_n, sec=sec_n)
            
            line_n = re.sub("..:..:..:...", date_n, line)
            
            # calculate L2 Hit ratio
            line_list = line_n.split(',')
            l2_hit_ratio_0 = float(line_list[19]) / (float(line_list[19]) + float(line_list[15])) * 100
            l2_hit_ratio_0 = str(round(l2_hit_ratio_0, 2))
            l2_hit_ratio_1 = float(line_list[41]) / (float(line_list[41]) + float(line_list[37])) * 100
            l2_hit_ratio_1 = str(round(l2_hit_ratio_1, 2))

            line_list[-1] = l2_hit_ratio_0
            line_list.append(l2_hit_ratio_1)
            line_list.append('\n')
            line_n = ",".join(line_list)
            f_new.write(line_n)
            
    f.close()
    f_new.close()
    
# reformat uProf timechart output (power profile)
def uprof_timechart_formatter(file, newfile):
    f = open(file,"r")
    f_new = open(newfile,"w")

    header = True
    for line in f:
        # get & reformat full date
        if "Profile Start Time:" in line:
            full_date = line.split(',')[1]
            month = month2num(full_date[0:3])
            date = int(full_date[4:6])
            year = int(full_date[7:11])
            full_date_new = "{year}-{month:02d}-{date}".format(year=year, month=month, date=date)

        # Reformat timestamps
        if not header:
            timestamp_n = line.split(',')[1]
            timestamp_n = timestamp_n.split(':')
            hour_n = int(timestamp_n[0])
            min_n = int(timestamp_n[1])
            sec_n = int(timestamp_n[2])
            date_n = ",{year_month_day} {hour:02d}:{min:02d}:{sec:02d},".format(year_month_day=full_date_new, hour=hour_n, min=min_n, sec=sec_n)

            line_n = re.sub(",.*:.*:.*:...,", date_n, line)
            f_new.write(line_n)

        # header=False indicates next line is data
        if "Timestamp" in line:
            header = False
            f_new.write(line)

    f.close()
    f_new.close()


# convert 3 letter month str to a number
def month2num(month_str):
    if month_str=="Jan":
        return 1
    elif month_str=="Feb":
        return 2
    elif month_str=="Mar":
        return 3
    elif month_str=="Apr":
        return 4
    elif month_str=="May":
        return 5
    elif month_str=="Jun":
        return 6
    elif month_str=="Jul":
        return 7
    elif month_str=="Aug":
        return 8
    elif month_str=="Sep":
        return 9
    elif month_str=="Oct":
        return 10
    elif month_str=="Nov":
        return 11
    elif month_str=="Dec":
        return 12
    else:
        print("Warning: invalid month")


def main():
    args=sys.argv

    if len(args) != 5:
        print("Usage: {} pcm_file pcm_newfile timechart_file timechart_newfile".format(args[0]))
    elif len(args) == 5:
        uprof_pcm_formatter(args[1], args[2])
        uprof_timechart_formatter(args[3], args[4])

if __name__ == "__main__":
    main()



