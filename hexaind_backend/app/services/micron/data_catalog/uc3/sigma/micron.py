def trav_search(FAB, traveler_df, l, debug=False):

    traveler_df.rename(columns={"MfgArea": "Mfg Area"}, inplace=True)
    df_area_filter = traveler_df[
        traveler_df["Mfg Area"].isin(
            [
                f"F{FAB} DIFFUSION",
                f"F{FAB} WET PROCESS",
                f"F{FAB} PHOTO",
                f"F{FAB} DRY ETCH",
                f"F{FAB} METROLOGY",
                f"F{FAB} IMPLANT",
                f"F{FAB} CVD",
                f"F{FAB} CMP",
                f"F{FAB} PVD",
            ]
        )
    ]
    df_area_filter.reset_index(drop=True, inplace=True)

    list_of_strings = ["COAT", "SCRUB", "CLN"]
    dicto = {}
    for j in l:
        try:
            idx = df_area_filter.index[df_area_filter.Step == j]
            if debug:
                print(f"Current metro step index:{idx[0]}")
                print("Current metro:", j)
                print(
                    "Current corresponding Mfg Area :",
                    df_area_filter.loc[idx[0], "Mfg Area"],
                )

            if df_area_filter.loc[idx[0], "Mfg Area"] == f"F{FAB} PHOTO":
                for i in range(idx[0], -1, -1):
                    if (
                        (df_area_filter.loc[i, "Mfg Area"] == f"F{FAB} PHOTO")
                        and (
                            df_area_filter.loc[i, "Step"].startswith(
                                ("3", "4", "5", "6", "7", "8", "9")
                            )
                        )
                    ) or (
                        df_area_filter.loc[i, "Mfg Area"]
                        in [
                            f"F{FAB} DIFFUSION",
                            f"F{FAB} WET PROCESS",
                            f"F{FAB} DRY ETCH",
                            f"F{FAB} IMPLANT",
                            f"F{FAB} CVD",
                            f"F{FAB} CMP",
                            f"F{FAB} PVD",
                        ]
                    ):
                        if not any(
                            substring.lower() in df_area_filter.loc[i, "Step"].lower()
                            for substring in list_of_strings
                        ):
                            dicto[df_area_filter.loc[idx[0], "Step"]] = (
                                df_area_filter.loc[i, "Step"]
                            )
                            break
                    else:
                        pass
            elif df_area_filter.loc[idx[0], "Mfg Area"] == f"F{FAB} METROLOGY":
                for i in range(idx[0], -1, -1):
                    if df_area_filter.loc[i, "Mfg Area"] in [
                        f"F{FAB} DIFFUSION",
                        f"F{FAB} WET PROCESS",
                        f"F{FAB} DRY ETCH",
                        f"F{FAB} IMPLANT",
                        f"F{FAB} CVD",
                        f"F{FAB} CMP",
                        f"F{FAB} PVD",
                    ]:
                        if not any(
                            substring.lower() in df_area_filter.loc[i, "Step"].lower()
                            for substring in list_of_strings
                        ):
                            dicto[df_area_filter.loc[idx[0], "Step"]] = (
                                df_area_filter.loc[i, "Step"]
                            )
                            break
                    else:
                        pass
        except Exception as e:
            if debug:
                print(e)
            pass
        try:
            x = j.split()
            string = x[0] + " " + x[1]
            if debug:
                print("String in try:", string)
            idx = df_area_filter.index[df_area_filter.Step.str.contains(string)]
            if debug:
                print(f"New metro step index:{idx[0]}")
                print("Current metro:", j)
                print(
                    "New corresponding Mfg Area :",
                    df_area_filter.loc[idx[0], "Mfg Area"],
                )
                print("New metro:", df_area_filter.loc[idx[0], "Step"])
            if df_area_filter.loc[idx[0], "Mfg Area"] == f"F{FAB} PHOTO":
                for i in range(idx[0], -1, -1):
                    if (
                        (df_area_filter.loc[i, "Mfg Area"] == f"F{FAB} PHOTO")
                        and (
                            df_area_filter.loc[i, "Step"].startswith(
                                ("3", "4", "5", "6", "7", "8", "9")
                            )
                        )
                    ) or (
                        df_area_filter.loc[i, "Mfg Area"]
                        in [
                            f"F{FAB} DIFFUSION",
                            f"F{FAB} WET PROCESS",
                            f"F{FAB} DRY ETCH",
                            f"F{FAB} IMPLANT",
                            f"F{FAB} CVD",
                            f"F{FAB} CMP",
                            f"F{FAB} PVD",
                        ]
                    ):
                        if not any(
                            substring.lower() in df_area_filter.loc[i, "Step"].lower()
                            for substring in list_of_strings
                        ):
                            dicto[j] = df_area_filter.loc[i, "Step"]
                            break
                    else:
                        pass
            elif df_area_filter.loc[idx[0], "Mfg Area"] == f"F{FAB} METROLOGY":
                for i in range(idx[0], -1, -1):
                    if df_area_filter.loc[i, "Mfg Area"] in [
                        f"F{FAB} DIFFUSION",
                        f"F{FAB} WET PROCESS",
                        f"F{FAB} DRY ETCH",
                        f"F{FAB} IMPLANT",
                        f"F{FAB} CVD",
                        f"F{FAB} CMP",
                        f"F{FAB} PVD",
                    ]:
                        if not any(
                            substring.lower() in df_area_filter.loc[i, "Step"].lower()
                            for substring in list_of_strings
                        ):
                            dicto[j] = df_area_filter.loc[i, "Step"]
                            break
                    else:
                        pass
        except Exception as e:
            x = j.split()
            string = x[0]
            if debug:
                print("String in exception:", string)
            try:
                if debug:
                    print(f"New metro step index:{idx[0]}")
                    print("Current metro:", j)
                    print(
                        "New corresponding Mfg Area :",
                        df_area_filter.loc[idx[0], "Mfg Area"],
                    )
                    print("New metro:", df_area_filter.loc[idx[0], "Step"])
                if df_area_filter.loc[idx[0], "Mfg Area"] == f"F{FAB} PHOTO":
                    for i in range(idx[0], -1, -1):
                        if (
                            (df_area_filter.loc[i, "Mfg Area"] == f"F{FAB} PHOTO")
                            and (
                                df_area_filter.loc[i, "Step"].startswith(
                                    ("3", "4", "5", "6", "7", "8", "9")
                                )
                            )
                        ) or (
                            df_area_filter.loc[i, "Mfg Area"]
                            in [
                                f"F{FAB} DIFFUSION",
                                f"F{FAB} WET PROCESS",
                                f"F{FAB} DRY ETCH",
                                f"F{FAB} IMPLANT",
                                f"F{FAB} CVD",
                                f"F{FAB} CMP",
                                f"F{FAB} PVD",
                            ]
                        ):
                            if not any(
                                substring.lower()
                                in df_area_filter.loc[i, "Step"].lower()
                                for substring in list_of_strings
                            ):
                                dicto[j] = df_area_filter.loc[i, "Step"]
                                break
                        else:
                            pass
                elif df_area_filter.loc[idx[0], "Mfg Area"] == f"F{FAB} METROLOGY":
                    for i in range(idx[0], -1, -1):
                        if df_area_filter.loc[i, "Mfg Area"] in [
                            f"F{FAB} DIFFUSION",
                            f"F{FAB} WET PROCESS",
                            f"F{FAB} DRY ETCH",
                            f"F{FAB} IMPLANT",
                            f"F{FAB} CVD",
                            f"F{FAB} CMP",
                            f"F{FAB} PVD",
                        ]:
                            if not any(
                                substring.lower()
                                in df_area_filter.loc[i, "Step"].lower()
                                for substring in list_of_strings
                            ):
                                dicto[j] = df_area_filter.loc[i, "Step"]
                                break
                        else:
                            pass
            except Exception as e:
                pass
    return dicto
